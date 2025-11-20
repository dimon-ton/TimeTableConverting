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
from src.utils.sheet_utils import log_request_to_sheet


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

    # Save group ID if this is the target group (for first-time setup)
    if group_id and not config.LINE_GROUP_ID:
        print(f"\nNOTE: Add this to your .env file:")
        print(f"LINE_GROUP_ID={group_id}\n")

    # Process leave request
    process_leave_request_message(text, group_id, reply_token)


def process_leave_request_message(text: str, group_id: str, reply_token: str):
    """
    Process a potential leave request message, log it to the Leave_Requests
    sheet, and send a confirmation reply.
    """
    # Check if this is from the configured group (if set)
    if config.LINE_GROUP_ID and group_id != config.LINE_GROUP_ID:
        print(f"Ignoring message from non-target group: {group_id}")
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
            send_reply(
                reply_token,
                "ขออภัยค่ะ ไม่เข้าใจข้อความ กรุณาระบุ: ชื่อครู, วันที่, และคาบที่ลา\n"
                "ตัวอย่าง: ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3"
            )
            return

        # 3. Send confirmation to user
        teacher_name = leave_data.get('teacher_name', 'N/A')
        date_str = leave_data.get('date', 'N/A')
        periods = leave_data.get('periods', [])
        periods_str = ", ".join(map(str, periods))

        confirmation = (
            f"✓ ได้รับเรื่องขอลาของ {teacher_name} เรียบร้อยแล้ว\n\n"
            f"วันที่: {date_str}\n"
            f"คาบ: {periods_str}\n\n"
            f"ระบบจะประมวลผลและจัดหาครูสอนแทนในขั้นตอนถัดไป"
        )
        send_reply(reply_token, confirmation)
        print("Leave request logged successfully to 'Leave_Requests' sheet.")

    except Exception as e:
        print(f"ERROR processing leave request: {e}")
        import traceback
        traceback.print_exc()

        send_reply(
            reply_token,
            "เกิดข้อผิดพลาดในการประมวลผล กรุณาติดต่อผู้ดูแลระบบ"
        )


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
