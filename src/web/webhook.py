"""
LINE Bot Webhook Server

Flask server that receives LINE messages and processes leave requests.

Features:
- Receives webhook events from LINE Messaging API
- Verifies signatures for security
- Parses leave requests using AI (OpenRouter/Gemini)
- Adds absences to Google Sheets
- Sends confirmation messages back to LINE group

Usage:
    python webhook.py

    # With debug mode
    DEBUG_MODE=True python webhook.py
"""

import hashlib
import hmac
import base64
import json
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.config import config
from src.timetable.ai_parser import parse_leave_request, parse_leave_request_fallback
from src.utils.sheet_utils import (
    log_request_to_sheet,
    finalize_pending_assignment,
    load_pending_assignments,
    update_pending_assignments,
    write_teacher_hours_snapshot
)
from src.utils.report_parser import (
    parse_edited_assignments,
    detect_assignment_changes,
    generate_confirmation_message,
    load_teacher_name_map,
    load_teacher_full_names
)


# Initialize Flask app
app = Flask(__name__)

# Initialize LINE Bot API (v3)
if config.LINE_CHANNEL_ACCESS_TOKEN:
    configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
    api_client = ApiClient(configuration)
    line_bot_api = MessagingApi(api_client)
else:
    line_bot_api = None
    print("WARNING: LINE_CHANNEL_ACCESS_TOKEN not set")

# Initialize Webhook Handler (v3)
if config.LINE_CHANNEL_SECRET:
    handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
else:
    handler = None
    print("WARNING: LINE_CHANNEL_SECRET not set")


def verify_signature(body: bytes, signature: str) -> bool:
    """
    Verify that the request came from LINE.

    Args:
        body: Request body as bytes
        signature: X-Line-Signature header value

    Returns:
        True if signature is valid, False otherwise
    """
    if not config.LINE_CHANNEL_SECRET:
        print("WARNING: Cannot verify signature - LINE_CHANNEL_SECRET not set")
        return config.DEBUG_MODE  # Allow in debug mode

    hash_digest = hmac.new(
        config.LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(hash_digest).decode('utf-8')

    return hmac.compare_digest(signature, expected_signature)


def is_substitution_report(text: str) -> bool:
    """
    Check if message is a substitution report.

    Args:
        text: Message text

    Returns:
        True if message starts with REPORT_PREFIX
    """
    return text.strip().startswith(config.REPORT_PREFIX)


def parse_report_date(text: str) -> str:
    """
    Extract date from report message.

    Expected format: [REPORT] YYYY-MM-DD (with optional additional text on following lines)

    Args:
        text: Report message (can be multi-line)

    Returns:
        Date string in YYYY-MM-DD format, or None if invalid
    """
    import re

    # Get the first line only
    first_line = text.strip().split('\n')[0].strip()

    if not first_line.startswith(config.REPORT_PREFIX):
        return None

    # Extract everything after the prefix on the first line
    date_part = first_line[len(config.REPORT_PREFIX):].strip()

    # Validate YYYY-MM-DD format
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(date_pattern, date_part):
        return date_part

    return None


def process_substitution_report(text: str, group_id: str, user_id: str):
    """
    Process admin substitution report and finalize pending assignments.

    Args:
        text: Report message text
        group_id: LINE group ID where message was sent
        user_id: LINE user ID of sender (admin)
    """
    # Only accept reports from teacher group (admins send to teacher group)
    teacher_group = config.LINE_TEACHER_GROUP_ID or config.LINE_GROUP_ID
    if teacher_group and group_id != teacher_group:
        print(f"Ignoring report from non-teacher group: {group_id}")
        return

    try:
        # Parse date from message
        target_date = parse_report_date(text)

        if not target_date:
            print(f"Invalid report format: {text}")
            send_to_admin(
                "❌ รูปแบบวันที่ไม่ถูกต้อง\n\n"
                "บรรทัดแรกต้องเป็น: [REPORT] YYYY-MM-DD\n"
                f"ตัวอย่าง:\n"
                f"[REPORT] 2025-11-28\n"
                f"รายงานการสอนแทน..."
            )
            return

        print(f"Processing substitution report for date: {target_date}")
        print(f"Verified by admin user: {user_id}")

        # Validate date is not in the future
        from datetime import datetime as dt
        try:
            report_date = dt.strptime(target_date, '%Y-%m-%d').date()
            today = dt.now().date()

            if report_date > today:
                send_to_admin(
                    f"❌ ไม่สามารถยืนยันวันที่ในอนาคต\n\n"
                    f"วันที่ในรายงาน: {target_date}\n"
                    f"วันนี้: {today}\n\n"
                    f"กรุณาตรวจสอบวันที่ในรายงาน"
                )
                print(f"ERROR: Report date {target_date} is in the future")
                return

            # Check if date is too old (more than 7 days)
            days_diff = (today - report_date).days
            if days_diff > config.PENDING_EXPIRATION_DAYS:
                send_to_admin(
                    f"⚠️ วันที่ในรายงานเก่าเกินไป\n\n"
                    f"วันที่ในรายงาน: {target_date}\n"
                    f"เก่ากว่าวันนี้: {days_diff} วัน\n\n"
                    f"ข้อมูลอาจถูกลบหรือหมดอายุแล้ว (เกิน {config.PENDING_EXPIRATION_DAYS} วัน)"
                )
                print(f"WARNING: Report date {target_date} is {days_diff} days old")

        except ValueError:
            send_to_admin(
                f"❌ รูปแบบวันที่ไม่ถูกต้อง\n\n"
                f"วันที่: {target_date}\n\n"
                f"กรุณาใช้รูปแบบ YYYY-MM-DD"
            )
            return

        # === NEW: Parse admin edits and update database ===

        # Load teacher mappings
        print("Loading teacher mappings...")
        teacher_name_map = load_teacher_name_map()
        teacher_full_names = load_teacher_full_names()

        # Parse assignments from message
        print("Parsing assignments from edited message...")
        parsed_assignments = parse_edited_assignments(text)
        print(f"Parsed {len(parsed_assignments)} assignments from message")

        # Load pending assignments
        print(f"Loading pending assignments for {target_date}...")
        pending_assignments = load_pending_assignments(target_date)

        if not pending_assignments:
            send_to_admin(
                f"ℹ️ ไม่พบข้อมูลการสอนแทนที่รอการยืนยัน\n\n"
                f"วันที่: {target_date}\n\n"
                f"อาจเป็นเพราะ:\n"
                f"- ไม่มีข้อมูลสำหรับวันที่นี้\n"
                f"- ข้อมูลถูกยืนยันไปแล้ว\n"
                f"- ข้อมูลหมดอายุ (เกิน {config.PENDING_EXPIRATION_DAYS} วัน)"
            )
            print(f"No pending assignments found for {target_date}")
            return

        print(f"Found {len(pending_assignments)} pending assignments")

        # Detect changes
        print("Detecting changes between parsed and pending assignments...")
        changes = detect_assignment_changes(
            target_date,
            parsed_assignments,
            pending_assignments,
            teacher_name_map,
            teacher_full_names,
            use_ai=config.USE_AI_MATCHING,
            api_key=config.OPENROUTER_API_KEY,
            ai_threshold=config.AI_MATCH_CONFIDENCE_THRESHOLD
        )

        print(f"Detected {len(changes['updated'])} updated assignments")
        print(f"Detected {len(changes['ai_suggestions'])} AI suggestions")
        print(f"Detected {len(changes['unchanged'])} unchanged assignments")
        print(f"Detected {len(changes['match_errors'])} match errors")

        # Update if changes detected
        update_summary = ""
        if changes['updated']:
            print(f"Updating {len(changes['updated'])} assignments in Pending_Assignments...")
            update_count, errors = update_pending_assignments(target_date, changes['updated'])

            if errors:
                print(f"Errors during update: {errors}")

            # Send confirmation message showing all changes
            print("Generating confirmation message...")
            confirmation = generate_confirmation_message(
                target_date,
                changes,
                teacher_full_names
            )
            send_to_admin(confirmation)

            update_summary = f"\n📝 อัปเดตครูสอนแทน: {len(changes['updated'])} คาบ\n"
            print(f"Successfully updated {update_count} assignments")
        else:
            print("No changes detected - proceeding with original assignments")

        # === END NEW SECTION ===

        # Finalize pending assignments (existing code)
        finalized_count = finalize_pending_assignment(target_date, verified_by=user_id)

        if finalized_count > 0:
            # Write teacher hours snapshot after finalization completes
            try:
                write_teacher_hours_snapshot(target_date)
                print(f"Successfully updated teacher hours snapshot for {target_date}")
                snapshot_status = "และบันทึกข้อมูลชั่วโมงสอนเรียบร้อยแล้ว"
            except Exception as e:
                print(f"ERROR writing teacher hours snapshot: {e}")
                snapshot_status = "แต่เกิดข้อผิดพลาดในการบันทึกข้อมูลชั่วโมงสอน"

            # Send confirmation to admin group (updated to include edit summary)
            send_to_admin(
                f"✅ ยืนยันการสอนแทนสำเร็จ\n\n"
                f"วันที่: {target_date}\n"
                f"จำนวน: {finalized_count} คาบ"
                f"{update_summary}\n"
                f"ข้อมูลถูกบันทึกลงใน Leave_Logs {snapshot_status}"
            )
            print(f"Successfully finalized {finalized_count} assignments for {target_date}")
        else:
            # No pending assignments found
            send_to_admin(
                f"ℹ️ ไม่พบข้อมูลการสอนแทนที่รอการยืนยัน\n\n"
                f"วันที่: {target_date}\n\n"
                f"อาจเป็นเพราะ:\n"
                f"- ไม่มีข้อมูลสำหรับวันที่นี้\n"
                f"- ข้อมูลถูกยืนยันไปแล้ว\n"
                f"- ข้อมูลหมดอายุ (เกิน {config.PENDING_EXPIRATION_DAYS} วัน)"
            )
            print(f"No pending assignments found for {target_date}")

    except Exception as e:
        print(f"ERROR processing substitution report: {e}")
        import traceback
        traceback.print_exc()

        send_to_admin(
            f"⚠️ เกิดข้อผิดพลาดในการประมวลผล\n\n"
            f"ข้อความ: {text}\n\n"
            f"Error: {str(e)}"
        )


@app.route("/callback", methods=['POST'])
def callback():
    """
    LINE webhook callback endpoint.

    Receives events from LINE and processes them.
    """
    # Get request body and signature
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')

    # Log incoming request (in debug mode)
    if config.DEBUG_MODE:
        print(f"\n{'='*60}")
        print("Incoming Webhook Event")
        print(f"{'='*60}")
        print(f"Signature: {signature}")
        print(f"Body: {body}")
        print(f"{'='*60}\n")

    # Verify signature
    if not verify_signature(body.encode('utf-8'), signature):
        print("ERROR: Invalid signature")
        abort(400)

    # Handle webhook body
    try:
        if handler:
            handler.handle(body, signature)
        else:
            # Manual handling if webhook handler not initialized
            process_webhook_manually(json.loads(body))

    except InvalidSignatureError:
        print("ERROR: Invalid signature error")
        abort(400)
    except Exception as e:
        print(f"ERROR processing webhook: {e}")
        import traceback
        traceback.print_exc()

    return 'OK'


def process_webhook_manually(webhook_data: dict):
    """
    Manually process webhook when handler is not available.

    Args:
        webhook_data: Parsed JSON webhook data
    """
    for event in webhook_data.get('events', []):
        if event.get('type') == 'message' and event['message']['type'] == 'text':
            text = event['message']['text']
            source = event.get('source', {})
            group_id = source.get('groupId', '')

            print(f"\nReceived message: {text}")
            print(f"Group ID: {group_id}")

            # Process the message
            process_leave_request_message(text, group_id, event.get('replyToken'))


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    Handle incoming text messages.

    Args:
        event: LINE message event
    """
    # Get message text
    text = event.message.text

    # Get source information
    source = event.source
    group_id = getattr(source, 'group_id', None)
    user_id = getattr(source, 'user_id', None)
    reply_token = event.reply_token

    # Log message
    print(f"\n{'='*60}")
    print(f"Received Message")
    print(f"{'='*60}")
    print(f"Text: {text}")
    print(f"Group ID: {group_id}")
    print(f"User ID: {user_id}")
    print(f"{'='*60}\n")

    # Save group ID suggestions (for first-time setup)
    if group_id:
        if not config.LINE_TEACHER_GROUP_ID:
            print(f"\nNOTE: Add teacher group to your .env file:")
            print(f"LINE_TEACHER_GROUP_ID={group_id}\n")
        if not config.LINE_ADMIN_GROUP_ID:
            print(f"\nNOTE: Add admin group to your .env file:")
            print(f"LINE_ADMIN_GROUP_ID={group_id}\n")

    # Check for substitution report FIRST
    if is_substitution_report(text):
        process_substitution_report(text, group_id, user_id)
        return

    # Otherwise, process as leave request
    process_leave_request_message(text, group_id, reply_token)


def process_leave_request_message(text: str, group_id: str, reply_token: str):
    """
    Process a potential leave request message, log it to the Leave_Requests
    sheet, and send a confirmation to admin group.
    """
    # Only accept messages from teacher group
    # Fallback to LINE_GROUP_ID for backward compatibility
    teacher_group = config.LINE_TEACHER_GROUP_ID or config.LINE_GROUP_ID
    if teacher_group and group_id != teacher_group:
        print(f"Ignoring message from non-teacher group: {group_id}")
        return

    # Check if message looks like a leave request
    leave_keywords = ['ลา', 'ขอลา', 'หยุด', 'ไม่มา']
    if not any(keyword in text for keyword in leave_keywords):
        print(f"Message doesn't look like a leave request: {text}")
        return

    try:
        # 1. Parse leave request (with fallback)
        print("Parsing leave request...")
        leave_data = parse_leave_request(text)
        status = "Success (AI)"
        if not leave_data:
            print("AI parsing failed. Trying fallback parser...")
            leave_data = parse_leave_request_fallback(text)
            status = "Success (Fallback)"

        # 2. Log the parsing attempt to "Leave_Requests" sheet
        if leave_data:
            log_request_to_sheet(raw_message=text, leave_data=leave_data, status=status)
        else:
            log_request_to_sheet(raw_message=text, leave_data=None, status="Failed")
            print("Failed to parse leave request with any method.")
            send_to_admin(
                "❌ การแจ้งลาล้มเหลว\n\n"
                f"ข้อความ: {text}\n\n"
                "ไม่สามารถแยกข้อมูล: ชื่อครู, วันที่, และคาบที่ลา"
            )
            return

        # 3. Send confirmation to admin group
        teacher_name = leave_data.get('teacher_name', 'N/A')
        date_str = leave_data.get('date', 'N/A')
        periods = leave_data.get('periods', [])
        periods_str = ", ".join(map(str, periods))

        confirmation = (
            f"📝 ได้รับเรื่องขอลาใหม่\n\n"
            f"ครู: {teacher_name}\n"
            f"วันที่: {date_str}\n"
            f"คาบ: {periods_str}\n\n"
            f"✓ บันทึกเรียบร้อยแล้ว (ใช้ AI {status})"
        )
        send_to_admin(confirmation)
        print("Leave request logged successfully to 'Leave_Requests' sheet.")

    except Exception as e:
        print(f"ERROR processing leave request: {e}")
        import traceback
        traceback.print_exc()

        send_to_admin(
            f"⚠️ เกิดข้อผิดพลาดในการประมวลผล\n\n"
            f"ข้อความ: {text}\n\n"
            f"Error: {str(e)}"
        )


def send_to_admin(text: str):
    """
    Send a push message to the admin group.

    Args:
        text: Message text to send to admin group
    """
    from src.web.line_messaging import send_to_admin_group

    admin_group = config.LINE_ADMIN_GROUP_ID or config.LINE_GROUP_ID
    if not admin_group:
        print(f"Would send to admin: {text}")
        return

    try:
        send_to_admin_group(text)
        print(f"Sent to admin group: {text}")
    except Exception as e:
        print(f"ERROR sending to admin: {e}")


def send_reply(reply_token: str, text: str):
    """
    Send a reply message to LINE.

    Args:
        reply_token: Reply token from webhook event
        text: Message text to send
    """
    if not line_bot_api or not reply_token:
        print(f"Would send reply: {text}")
        return

    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )
        print(f"Sent reply: {text}")
    except Exception as e:
        print(f"ERROR sending reply: {e}")


@app.route("/")
def home():
    """Home page - basic health check"""
    return "LINE Bot Webhook Server is running!"


@app.route("/health")
def health():
    """Health check endpoint"""
    status = {
        "status": "ok",
        "line_bot_api": "configured" if line_bot_api else "not configured",
        "webhook_handler": "configured" if handler else "not configured",
        "spreadsheet_id": config.SPREADSHEET_ID[:20] + "..." if config.SPREADSHEET_ID else "not set"
    }
    return json.dumps(status, ensure_ascii=False)


def main():
    """Start the Flask server"""
    print("="*60)
    print("LINE Bot Webhook Server")
    print("="*60)

    # Print configuration status
    config.print_status()

    # Check for critical errors
    errors = config.validate()
    if errors and not config.DEBUG_MODE:
        print("\nERROR: Configuration incomplete:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease set up your .env file before running.")
        print("See LINE_BOT_SETUP.md for instructions.")
        return

    # Start server
    print(f"\nStarting Flask server on {config.WEBHOOK_HOST}:{config.WEBHOOK_PORT}")
    print(f"Webhook endpoint: http://localhost:{config.WEBHOOK_PORT}/callback")
    print(f"Debug mode: {config.DEBUG_MODE}")
    print("\nPress Ctrl+C to stop\n")

    app.run(
        host=config.WEBHOOK_HOST,
        port=config.WEBHOOK_PORT,
        debug=config.DEBUG_MODE
    )


if __name__ == "__main__":
    main()
