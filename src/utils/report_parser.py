"""
Report Parser Module

Parses admin-edited report messages to detect changes in substitute teacher assignments.
Includes 4-tier matching: exact → normalized → fuzzy → AI-powered matching.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import requests
from pathlib import Path

# Compile regex patterns once at module level for performance
ASSIGNMENT_PATTERN = re.compile(
    r'วิชา(.+?)\s*\((.+?)\):\s*(.+?)\s*\(ลา\)\s*➡️\s*(.+?)\s*\(สอนแทน\)'
)
DAY_PATTERN = re.compile(r'วัน(จันทร์|อังคาร|พุธ|พฤหัสบดี|ศุกร์):')
PERIOD_PATTERN = re.compile(r'คาบที่\s*(\d+):')
NO_SUBSTITUTE_PATTERN = re.compile(r'❌\s*ไม่พบครูสอนแทน')

# Thai day name to English mapping
DAY_MAP = {
    'จันทร์': 'Mon',
    'อังคาร': 'Tue',
    'พุธ': 'Wed',
    'พฤหัสบดี': 'Thu',
    'ศุกร์': 'Fri'
}

# Cache for teacher mappings (loaded once per module)
_teacher_name_map_cache = None
_teacher_full_names_cache = None


def load_teacher_name_map() -> Dict[str, str]:
    """Load teacher name to ID mapping from JSON file."""
    global _teacher_name_map_cache
    if _teacher_name_map_cache is None:
        data_path = Path(__file__).parent.parent.parent / 'data' / 'teacher_name_map.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            _teacher_name_map_cache = json.load(f)
    return _teacher_name_map_cache


def load_teacher_full_names() -> Dict[str, str]:
    """Load teacher ID to full name mapping."""
    global _teacher_full_names_cache
    if _teacher_full_names_cache is None:
        data_path = Path(__file__).parent.parent.parent / 'data' / 'teacher_full_names.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            _teacher_full_names_cache = json.load(f)
    return _teacher_full_names_cache


def normalize_thai_name(name: str) -> str:
    """
    Normalize Thai teacher name for matching.
    Remove "ครู" prefix, strip whitespace, lowercase.
    """
    normalized = name.strip()
    if normalized.startswith('ครู'):
        normalized = normalized[3:]  # Remove "ครู" (3 chars in Thai)
    return normalized.strip().lower()


def fuzzy_match_score(str1: str, str2: str) -> float:
    """Calculate fuzzy match score between two strings using SequenceMatcher."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def ai_fuzzy_match_teacher(
    misspelled_name: str,
    valid_teacher_names: List[str],
    api_key: str,
    model: str = "anthropic/claude-3.5-sonnet"
) -> Tuple[Optional[str], float, str]:
    """
    Use OpenRouter API to match potentially misspelled teacher name.

    Args:
        misspelled_name: The potentially misspelled teacher name
        valid_teacher_names: List of valid teacher names to match against
        api_key: OpenRouter API key
        model: Model to use for matching

    Returns:
        Tuple of (matched_name, confidence, reasoning)
    """
    try:
        prompt = f"""You are a Thai name matching expert. Given a potentially misspelled Thai teacher name and a list of valid teacher names, find the best match.

Misspelled name: "{misspelled_name}"

Valid teacher names:
{chr(10).join(f"- {name}" for name in valid_teacher_names)}

Respond with JSON only:
{{
  "matched_name": "ครูสุจิตร",
  "confidence": 0.95,
  "reasoning": "Very similar spelling, likely typo in one character"
}}

If no reasonable match exists, set matched_name to null and confidence to 0."""

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Low temperature for consistent matching
                "max_tokens": 200
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']

            # Parse JSON from response
            # Handle markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            data = json.loads(content)
            matched_name = data.get('matched_name')
            confidence = float(data.get('confidence', 0))
            reasoning = data.get('reasoning', '')

            return (matched_name, confidence, reasoning)
        else:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return (None, 0.0, f"API error: {response.status_code}")

    except Exception as e:
        print(f"Error in AI fuzzy matching: {e}")
        return (None, 0.0, f"Exception: {str(e)}")


def match_teacher_name_to_id(
    thai_name: str,
    teacher_name_map: Dict[str, str],
    teacher_full_names: Dict[str, str],
    use_ai: bool = True,
    api_key: Optional[str] = None,
    ai_model: str = "anthropic/claude-3.5-sonnet"
) -> Tuple[Optional[str], float, str]:
    """
    Match Thai teacher name to teacher ID using 4-tier matching strategy.

    Tier 1: Exact match
    Tier 2: Normalized match (remove "ครู", trim, lowercase)
    Tier 3: Fuzzy match (string similarity >= 0.85)
    Tier 4: AI-powered fuzzy match (OpenRouter API)

    Args:
        thai_name: Thai teacher name from edited message
        teacher_name_map: Thai name → Teacher ID mapping
        teacher_full_names: Teacher ID → Thai name mapping (for reverse lookup)
        use_ai: Whether to use AI matching as last resort
        api_key: OpenRouter API key (required if use_ai=True)
        ai_model: OpenRouter model to use

    Returns:
        Tuple of (teacher_id, confidence, match_method)
        - teacher_id: T001-T018 or None
        - confidence: 0.0-1.0
        - match_method: 'exact', 'normalized', 'fuzzy', 'ai_fuzzy', or 'not_found'
    """
    if not thai_name or thai_name.strip() == '':
        return (None, 0.0, 'not_found')

    thai_name = thai_name.strip()

    # Tier 1: Exact match
    if thai_name in teacher_name_map:
        return (teacher_name_map[thai_name], 1.0, 'exact')

    # Tier 2: Normalized match
    normalized_input = normalize_thai_name(thai_name)
    for valid_name, teacher_id in teacher_name_map.items():
        normalized_valid = normalize_thai_name(valid_name)
        if normalized_input == normalized_valid:
            return (teacher_id, 0.95, 'normalized')

    # Tier 3: Fuzzy match (threshold 0.85)
    best_match = None
    best_score = 0.0

    for valid_name, teacher_id in teacher_name_map.items():
        score = fuzzy_match_score(thai_name, valid_name)
        if score > best_score:
            best_score = score
            best_match = teacher_id

    if best_score >= 0.85:
        return (best_match, best_score, 'fuzzy')

    # Tier 4: AI-powered fuzzy match (only if enabled and API key provided)
    if use_ai and api_key:
        valid_names = list(teacher_name_map.keys())
        matched_name, confidence, reasoning = ai_fuzzy_match_teacher(
            thai_name, valid_names, api_key, ai_model
        )

        if matched_name and matched_name in teacher_name_map:
            teacher_id = teacher_name_map[matched_name]
            return (teacher_id, confidence, 'ai_fuzzy')

    # No match found
    return (None, 0.0, 'not_found')


def parse_edited_assignments(report_text: str) -> List[Dict]:
    """
    Parse edited report message to extract substitute teacher assignments.

    Args:
        report_text: The full report message text

    Returns:
        List of parsed assignments with structure:
        {
            'subject_thai': str,
            'class_id': str,
            'absent_teacher_name': str,
            'substitute_teacher_name': str or None,
            'day': str,  # 'Mon', 'Tue', etc.
            'period': int
        }
    """
    assignments = []
    lines = report_text.split('\n')

    current_day = None
    current_period = None

    for line in lines:
        line = line.strip()

        # Check for day header
        day_match = DAY_PATTERN.search(line)
        if day_match:
            thai_day = day_match.group(1)
            current_day = DAY_MAP.get(thai_day)
            continue

        # Check for period header
        period_match = PERIOD_PATTERN.search(line)
        if period_match:
            current_period = int(period_match.group(1))
            continue

        # Check for assignment line
        assignment_match = ASSIGNMENT_PATTERN.search(line)
        if assignment_match and current_day and current_period:
            subject_thai = assignment_match.group(1).strip()
            class_id = assignment_match.group(2).strip()
            absent_teacher = assignment_match.group(3).strip()
            substitute_teacher = assignment_match.group(4).strip()

            # Check if it's the "no substitute" case
            if NO_SUBSTITUTE_PATTERN.search(substitute_teacher):
                substitute_teacher = None

            assignments.append({
                'subject_thai': subject_thai,
                'class_id': class_id,
                'absent_teacher_name': absent_teacher,
                'substitute_teacher_name': substitute_teacher,
                'day': current_day,
                'period': current_period
            })

    return assignments


def detect_assignment_changes(
    target_date: str,
    parsed_assignments: List[Dict],
    pending_assignments: List[Dict],
    teacher_name_map: Dict[str, str],
    teacher_full_names: Dict[str, str],
    use_ai: bool = True,
    api_key: Optional[str] = None,
    ai_threshold: float = 0.85
) -> Dict[str, List[Dict]]:
    """
    Compare parsed assignments with pending assignments to detect changes.

    Args:
        target_date: Date in YYYY-MM-DD format
        parsed_assignments: Assignments parsed from message
        pending_assignments: Assignments from Pending_Assignments sheet
        teacher_name_map: Thai name → Teacher ID mapping
        teacher_full_names: Teacher ID → Thai name mapping
        use_ai: Whether to use AI matching
        api_key: OpenRouter API key
        ai_threshold: Confidence threshold for auto-accepting AI matches

    Returns:
        Dict with keys:
        - 'updated': Assignments with different substitute teacher (high confidence)
        - 'ai_suggestions': Assignments with AI suggestions needing review (0.60-0.84 confidence)
        - 'unchanged': Assignments with same substitute teacher
        - 'not_found': Parsed assignments not found in pending
        - 'match_errors': Teacher names that couldn't be matched
    """
    # Build composite key lookup for pending assignments
    pending_lookup = {}
    for pending in pending_assignments:
        key = (
            pending.get('Date'),
            pending.get('Absent_Teacher'),
            pending.get('Day'),
            int(pending.get('Period', 0))
        )
        pending_lookup[key] = pending

    updated = []
    ai_suggestions = []
    unchanged = []
    not_found = []
    match_errors = []

    # Process each parsed assignment
    for parsed in parsed_assignments:
        # Match teacher names to IDs
        absent_id, absent_conf, absent_method = match_teacher_name_to_id(
            parsed['absent_teacher_name'],
            teacher_name_map,
            teacher_full_names,
            use_ai=use_ai,
            api_key=api_key
        )

        if not absent_id:
            match_errors.append({
                'teacher_name': parsed['absent_teacher_name'],
                'context': f"{parsed['subject_thai']} ({parsed['class_id']}) - {parsed['day']} คาบ {parsed['period']}"
            })
            continue

        # Match substitute teacher (could be None if "Not Found")
        sub_id = None
        sub_conf = 0.0
        sub_method = 'not_found'

        if parsed['substitute_teacher_name']:
            sub_id, sub_conf, sub_method = match_teacher_name_to_id(
                parsed['substitute_teacher_name'],
                teacher_name_map,
                teacher_full_names,
                use_ai=use_ai,
                api_key=api_key
            )

        # Build composite key
        key = (target_date, absent_id, parsed['day'], parsed['period'])

        # Look up in pending assignments
        if key not in pending_lookup:
            not_found.append({
                'parsed': parsed,
                'absent_teacher_id': absent_id,
                'substitute_teacher_id': sub_id
            })
            continue

        pending = pending_lookup[key]
        old_substitute = pending.get('Substitute_Teacher', '')

        # Handle AI suggestions with low confidence (0.60-0.84)
        if sub_method == 'ai_fuzzy' and 0.60 <= sub_conf < ai_threshold:
            ai_suggestions.append({
                'date': target_date,
                'absent_teacher': absent_id,
                'day': parsed['day'],
                'period': parsed['period'],
                'class_id': parsed['class_id'],
                'subject': parsed['subject_thai'],
                'suggested_name': parsed['substitute_teacher_name'],
                'suggested_id': sub_id,
                'confidence': sub_conf,
                'old_substitute': old_substitute
            })
            continue

        # Compare substitute teachers
        if sub_id != old_substitute:
            updated.append({
                'date': target_date,
                'absent_teacher': absent_id,
                'day': parsed['day'],
                'period': parsed['period'],
                'class_id': parsed['class_id'],
                'subject': parsed['subject_thai'],
                'old_substitute': old_substitute,
                'new_substitute': sub_id or 'Not Found',
                'match_confidence': sub_conf,
                'match_method': sub_method
            })
        else:
            unchanged.append({
                'date': target_date,
                'absent_teacher': absent_id,
                'day': parsed['day'],
                'period': parsed['period'],
                'class_id': parsed['class_id'],
                'subject': parsed['subject_thai'],
                'substitute': sub_id
            })

    return {
        'updated': updated,
        'ai_suggestions': ai_suggestions,
        'unchanged': unchanged,
        'not_found': not_found,
        'match_errors': match_errors
    }


def generate_confirmation_message(
    target_date: str,
    changes: Dict[str, List[Dict]],
    teacher_full_names: Dict[str, str]
) -> str:
    """
    Generate confirmation message for admin showing detected changes.

    Args:
        target_date: Date in YYYY-MM-DD format
        changes: Result from detect_assignment_changes()
        teacher_full_names: Teacher ID → Thai name mapping

    Returns:
        Formatted Thai confirmation message
    """
    lines = []

    # Header
    lines.append("✅ อัปเดตการสอนแทนสำเร็จ")
    lines.append("")
    lines.append(f"วันที่: {target_date}")
    lines.append("")

    # Updated assignments
    if changes['updated']:
        lines.append(f"📝 การเปลี่ยนแปลง ({len(changes['updated'])} คาบ):")
        for change in changes['updated']:
            subject = change['subject']
            class_id = change['class_id']
            period = change['period']
            old_name = teacher_full_names.get(change['old_substitute'], change['old_substitute'])
            new_name = teacher_full_names.get(change['new_substitute'], change['new_substitute'])

            if change['new_substitute'] == 'Not Found':
                new_name = "ไม่พบครูสอนแทน"

            lines.append(f"- วิชา{subject} ({class_id}) คาบ {period}:")
            lines.append(f"  เปลี่ยนจาก {old_name} เป็น {new_name} ✅")
        lines.append("")

    # Unchanged assignments
    if changes['unchanged']:
        lines.append(f"✓ ไม่เปลี่ยนแปลง ({len(changes['unchanged'])} คาบ)")
        lines.append("")

    # AI suggestions for manual review
    if changes['ai_suggestions']:
        lines.append("🤖 AI แนะนำการแก้ไขชื่อ (กรุณาตรวจสอบ):")
        for suggestion in changes['ai_suggestions']:
            subject = suggestion['subject']
            class_id = suggestion['class_id']
            period = suggestion['period']
            suggested_name = suggestion['suggested_name']
            matched_name = teacher_full_names.get(suggestion['suggested_id'], suggestion['suggested_id'])
            confidence = int(suggestion['confidence'] * 100)

            lines.append(f"- \"{suggested_name}\" → คาดว่าคือ \"{matched_name}\" (ความมั่นใจ: {confidence}%)")
            lines.append(f"  วิชา{subject} ({class_id}) คาบ {period}")
        lines.append("")

    # Warnings
    warnings = []

    if changes['match_errors']:
        for error in changes['match_errors']:
            warnings.append(f"- ไม่พบครู \"{error['teacher_name']}\" ในระบบ")
            warnings.append(f"  {error['context']}")

    if changes['not_found']:
        for nf in changes['not_found']:
            parsed = nf['parsed']
            warnings.append(f"- ไม่พบข้อมูลในระบบที่ตรงกับ:")
            warnings.append(f"  {parsed['subject_thai']} ({parsed['class_id']}) - {parsed['day']} คาบ {parsed['period']}")

    if warnings:
        lines.append("⚠️ คำเตือน:")
        lines.extend(warnings)

    return "\n".join(lines)
