"""
AI-Powered Leave Request Parser

Uses OpenRouter API (Gemini free tier) to parse natural language Thai leave
requests into structured data.

Extracts:
- Teacher name
- Date (supports "พรุ่งนี้", specific dates, etc.)
- Periods (ranges like "1-3" or lists like "1, 3, 5")
- Reason (optional)

Usage:
    from ai_parser import parse_leave_request

    result = parse_leave_request("ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3")
    # Returns: {
    #     'teacher_name': 'ครูสุกฤษฎิ์',
    #     'date': '2025-11-21',
    #     'periods': [1, 2, 3],
    #     'reason': 'ลากิจ'
    # }
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.config import config


def load_teacher_names():
    """Load teacher full names for better identification."""
    try:
        with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
            teacher_data = json.load(f)
        # Create a mapping of names without 'ครู' prefix to full names
        name_mapping = {}
        for teacher_id, full_name in teacher_data.items():
            # Remove 'ครู' prefix for easier matching
            if full_name.startswith('ครู'):
                short_name = full_name[3:]  # Remove 'ครู'
                name_mapping[short_name] = full_name
        return name_mapping
    except Exception as e:
        print(f"Warning: Could not load teacher names: {e}")
        return {}


# Load teacher names for the prompt
TEACHER_NAMES = load_teacher_names()

# Create teacher list for the prompt
TEACHER_LIST = "\n".join([f"  - {full_name}" for full_name in TEACHER_NAMES.values()])

# System prompt template for the AI model
SYSTEM_PROMPT_TEMPLATE = """คุณเป็นผู้ช่วยวิเคราะห์ข้อความคำขอลาของครู ให้แปลงข้อความเป็น JSON ตามรูปแบบนี้:

{{
  "teacher_name": "ชื่อครู (ต้องมีคำว่า 'ครู' นำหน้า)",
  "date": "วันที่ในรูปแบบ YYYY-MM-DD",
  "periods": [รายการคาบเรียนเป็นตัวเลข],
  "reason": "เหตุผลการลา (ถ้าไม่ระบุให้ใช้ 'ลากิจ')",
  "leave_type": "ประเภท: 'leave' หรือ 'late'"
}}

กฎการแปลง:
1. ชื่อครู:
   - ให้คงคำว่า "ครู" นำหน้าชื่อไว้เสมอ (เช่น "ครูสุกฤษฎิ์" -> "ครูสุกฤษฎิ์")
   - ข้อความอาจไม่มีช่องว่างระหว่างวันที่กับชื่อครู (เช่น "วันนี้ครูวิยะดา" -> "ครูวิยะดา")
   - ให้ละเลยคำทักทาย "เรียนท่าน ผอ." หรือคำอื่นๆ ที่ไม่เกี่ยวข้อง
   - **สำคัญ**: เทียบชื่อครูที่มีอยู่ในระบบเพื่อความถูกต้อง:
{teacher_list}
   - ถ้าพบชื่อจริง (เช่น "จรรยาภรณ์ ภูกลาง", "นางสาวจรรยาภรณ์") ให้จับคู่กับชื่อครูที่มี "ครู" นำหน้า
     * ตัวอย่าง: "จรรยาภรณ์" หรือ "นางสาวจรรยาภรณ์ ภูกลาง" -> "ครูจรรยาภรณ์"
     * ตัวอย่าง: "วิยะดา" หรือ "นางวิยะดา" -> "ครูวิยะดา"

2. วันที่:
   - "พรุ่งนี้" = วันถัดจากวันนี้
   - "วันนี้" = วันนี้
   - "วันจันทร์" = จันทร์หน้าที่ใกล้ที่สุด
   - วันที่ชัดเจน (เช่น "21/11/2025") = แปลงเป็น YYYY-MM-DD

3. คาบเรียน:
   - "คาบ 1-3" = [1, 2, 3]
   - "คาบ 1, 3, 5" = [1, 3, 5]
   - "คาบ 2" = [2]
   - "ทั้งวัน" หรือ "เต็มวัน" หรือ "1 วัน" = [1, 2, 3, 4, 5, 6, 7, 8]
   - "เข้าสาย" = [1, 2, 3] (ขาดครึ่งวันเช้า)

4. ประเภทการลา (leave_type):
   - "เข้าสาย" หรือ "มาสาย" = "late"
   - อื่นๆ = "leave"

5. เหตุผล:
   - ถ้าไม่ระบุ ให้ใช้ "ลากิจ"
   - ถ้ามี "ป่วย" ให้ใช้ "ลาป่วย"
   - ถ้ามี "ธุระ" ให้ใช้ "ลากิจ"
   - ถ้ามี "เข้าสาย" หรือ "มาสาย":
     * ถ้ามีเหตุผลเฉพาะ (เช่น "ไปฟังผลตรวจสามี") ให้ระบุเหตุผลนั้น
     * ถ้าไม่มีเหตุผลเฉพาะ ให้ใช้ "เข้าสาย" เป็นเหตุผล

วันนี้คือ: {today}

ตอบเป็น JSON เท่านั้น ไม่ต้องอธิบาย"""


def get_date_from_thai_text(date_text: str, today: datetime) -> str:
    """
    Convert Thai date expression to YYYY-MM-DD format.

    Args:
        date_text: Thai date expression (e.g., "พรุ่งนี้", "วันจันทร์")
        today: Reference date (usually today)

    Returns:
        Date string in YYYY-MM-DD format
    """
    date_text_lower = date_text.lower()

    # Today
    if 'วันนี้' in date_text_lower:
        return today.strftime('%Y-%m-%d')

    # Tomorrow
    if 'พรุ่งนี้' in date_text_lower or 'พรุ่ง' in date_text_lower:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')

    # Specific day names (find next occurrence)
    day_names = {
        'จันทร์': 0,  # Monday
        'อังคาร': 1,  # Tuesday
        'พุธ': 2,     # Wednesday
        'พฤหัส': 3,   # Thursday
        'ศุกร์': 4,   # Friday
        'เสาร์': 5,   # Saturday
        'อาทิตย์': 6  # Sunday
    }

    for thai_day, weekday in day_names.items():
        if thai_day in date_text_lower:
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # If no match, return tomorrow as fallback
    return (today + timedelta(days=1)).strftime('%Y-%m-%d')


def parse_leave_request(message: str) -> Optional[Dict]:
    """
    Parse a Thai leave request message using AI.

    Args:
        message: Natural language leave request in Thai (can include formal greetings)

    Returns:
        Dictionary with keys: teacher_name, date, periods, reason, leave_type
        - teacher_name: Name with "ครู" prefix
        - date: Date in YYYY-MM-DD format
        - periods: List of period numbers
        - reason: Reason for leave
        - leave_type: 'leave' for regular leave, 'late' for late arrival
        Returns None if parsing fails

    Example:
        >>> parse_leave_request("ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3")
        {
            'teacher_name': 'ครูสุกฤษฎิ์',
            'date': '2025-11-21',
            'periods': [1, 2, 3],
            'reason': 'ลากิจ',
            'leave_type': 'leave'
        }

        >>> parse_leave_request("เรียนท่าน ผอ.วันนี้ครูวิยะดาขออนุญาตลากิจ 1 วันค่ะ")
        {
            'teacher_name': 'ครูวิยะดา',
            'date': '2025-11-25',
            'periods': [1, 2, 3, 4, 5, 6, 7, 8],
            'reason': 'ลากิจ',
            'leave_type': 'leave'
        }
    """
    if not config.OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set")
        return None

    # Get current date for context
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d (%A)')

    # Prepare system prompt with current date and teacher list
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        teacher_list=TEACHER_LIST,
        today=today_str
    )

    # Prepare API request
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.2,  # Low temperature for consistent parsing
        "max_tokens": 1000
    }

    try:
        # Call OpenRouter API
        response = requests.post(
            config.OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        # Parse response
        data = response.json()
        content = data['choices'][0]['message']['content']

        # Extract JSON from response (AI might wrap in markdown code blocks)
        if '```json' in content:
            # Extract from code block
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        # Parse JSON with better error handling
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON from AI: {e}")
            print(f"Raw content: {content}")
            return None

        # Validate required fields
        required_fields = ['teacher_name', 'date', 'periods']
        if not all(field in result for field in required_fields):
            print(f"ERROR: Missing required fields in AI response: {result}")
            return None

        # Ensure periods is a list of integers
        if isinstance(result['periods'], list):
            result['periods'] = [int(p) for p in result['periods']]
        else:
            print(f"ERROR: periods is not a list: {result['periods']}")
            return None

        # Set default reason if not provided
        if 'reason' not in result or not result['reason']:
            result['reason'] = 'ลากิจ'

        # Set default leave_type if not provided or empty
        if 'leave_type' not in result or not result['leave_type']:
            result['leave_type'] = 'leave'

        return result

    except requests.exceptions.RequestException as e:
        print(f"ERROR calling OpenRouter API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON response: {e}")
        print(f"Response content: {content}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_leave_request_fallback(message: str) -> Optional[Dict]:
    """
    Disabled regex fallback parser.

    This project now requires LLM parsing via OPENROUTER_API_KEY.
    Regex-based parsing is intentionally disabled.

    Args:
        message: Leave request message

    Returns:
        None. Use parse_leave_request instead.
    """
    del message
    print("Fallback parser disabled; use parse_leave_request with OPENROUTER_API_KEY.")
    return None


def test_parser():
    """Test the parser with sample messages"""
    test_messages = [
        # Original test messages
        "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3",
        "ครูอำพร ลาป่วยวันนี้ คาบ 2, 4, 6",
        "ครูกฤตชยากร ขอลาวันจันทร์ ทั้งวัน เพราะมีธุระ",
        "ครูพิมล ขอลาพรุ่งนี้คาบ 5",
        # Real LINE messages from teachers
        "เรียนท่าน ผอ.วันนี้ครูวิยะดาขออนุญาตลากิจ 1 วันค่ะ",
        "เรียนท่าน ผอ วันนี้ครูจุฑารัตน์ขออนุญาตเข้าสายไปฟังผลตรวจสามีค่ะ",
        # Late arrival without specific reason
        "เรียนท่าน ผอ. วันนี้ครูสมชายขออนุญาตเข้าสายค่ะ",
    ]

    print("="*60)
    print("Testing AI Parser")
    print("="*60)

    for msg in test_messages:
        print(f"\nInput: {msg}")
        result = parse_leave_request(msg)
        if result:
            print(f"Output: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("Output: Failed to parse")

    print("\n" + "="*60)


if __name__ == "__main__":
    test_parser()
