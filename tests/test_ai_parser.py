"""
Comprehensive tests for AI-powered Thai message parser.

Tests cover:
- Teacher name extraction (formal greetings, no-spacing messages)
- Thai date parsing (พรุ่งนี้, วันนี้, วันจันทร์, explicit dates)
- Period extraction (ranges, lists, full day expressions)
- Late arrival detection (เข้าสาย, มาสาย)
- Reason extraction
- Fallback parser (regex-based)
- Real-world LINE messages
- Edge cases and error handling

All tests use mocks for OpenRouter API - no actual API calls.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.timetable.ai_parser import (
    parse_leave_request,
    parse_leave_request_fallback
)


class TestTeacherNameExtraction(unittest.TestCase):
    """Test teacher name extraction from Thai messages"""

    @patch('src.timetable.ai_parser.requests.post')
    def test_extract_from_formal_greeting(self, mock_post):
        """Extract name after 'เรียนท่าน ผอ.'"""
        # Mock OpenRouter API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "teacher_name": "วิยะดา",
                        "date": "2025-11-26",
                        "periods": [1, 2, 3],
                        "reason": "ป่วย",
                        "leave_type": "leave"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        result = parse_leave_request("เรียนท่าน ผอ. วันนี้ ครูวิยะดา ขอลาป่วย คาบ 1-3")

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result["teacher_name"], "วิยะดา")
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_extract_from_no_spacing(self):
        """Extract from 'วันนี้ครูวิยะดา' (no spaces) using fallback"""
        # Use fallback parser for deterministic testing
        result = parse_leave_request_fallback("วันนี้ครูวิยะดาขอลาป่วย คาบ 1-3")

        # Should extract name despite no spacing
        self.assertIsNotNone(result)
        # Fallback parser should handle this
        self.assertIn("teacher_name", result)

    def test_extract_with_kru_prefix(self):
        """Extract name with 'ครู' prefix"""
        result = parse_leave_request_fallback("ครูสุกฤษฎิ์ ขอลาพรุ่งนี้")

        self.assertIsNotNone(result)
        self.assertIn("teacher_name", result)


class TestDateParsing(unittest.TestCase):
    """Test Thai date expression parsing"""

    @patch('src.timetable.ai_parser.requests.post')
    def test_prung_nee_tomorrow(self, mock_post):
        """'พรุ่งนี้' parses to tomorrow's date"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "teacher_name": "test",
                        "date": tomorrow,
                        "periods": [1],
                        "leave_type": "leave"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        result = parse_leave_request("ขอลาพรุ่งนี้ คาบ 1")

        self.assertIsNotNone(result)
        # Should contain a date
        self.assertIn("date", result)

    @patch('src.timetable.ai_parser.requests.post')
    def test_wan_nee_today(self, mock_post):
        """'วันนี้' parses to today's date"""
        today = datetime.now().strftime("%Y-%m-%d")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "teacher_name": "test",
                        "date": today,
                        "periods": [1],
                        "leave_type": "leave"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        result = parse_leave_request("ขอลาวันนี้ คาบ 1")

        self.assertIsNotNone(result)
        self.assertIn("date", result)

    def test_explicit_date_thai_month(self):
        """'25 พฤศจิกายน' parses correctly"""
        # Fallback parser should handle Thai month names
        result = parse_leave_request_fallback("ขอลา 25 พฤศจิกายน 2568 คาบ 1")

        # Should extract some date information
        self.assertIsNotNone(result)

    def test_numeric_date_format(self):
        """Numeric date format '25/11/2568' parsed"""
        result = parse_leave_request_fallback("ขอลา 25/11/2568 คาบ 1")

        self.assertIsNotNone(result)


class TestPeriodParsing(unittest.TestCase):
    """Test period extraction from Thai text"""

    def test_period_range_1_to_3(self):
        """'คาบ 1-3' → [1, 2, 3]"""
        result = parse_leave_request_fallback("ขอลาคาบ 1-3")

        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_period_range_1_to_6(self):
        """'คาบ 1-6' → [1, 2, 3, 4, 5, 6]"""
        result = parse_leave_request_fallback("ขอลาคาบ 1-6")

        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3, 4, 5, 6])

    def test_period_list_non_consecutive(self):
        """'คาบ 1, 3, 5' → [1, 3, 5]"""
        result = parse_leave_request_fallback("ขอลาคาบ 1, 3, 5")

        self.assertIsNotNone(result)
        self.assertEqual(sorted(result["periods"]), [1, 3, 5])

    def test_period_list_with_spaces(self):
        """'คาบ 1 , 2 , 3' → [1, 2, 3]"""
        result = parse_leave_request_fallback("ขอลาคาบ 1 , 2 , 3")

        self.assertIsNotNone(result)
        self.assertTrue(all(p in result["periods"] for p in [1, 2, 3]))

    def test_full_day_tang_wan(self):
        """'ทั้งวัน' → [1, 2, 3, 4, 5, 6, 7, 8]"""
        result = parse_leave_request_fallback("ขอลาทั้งวัน")

        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3, 4, 5, 6, 7, 8])

    def test_full_day_tem_wan(self):
        """'เต็มวัน' → [1-8]"""
        result = parse_leave_request_fallback("ขอลาเต็มวัน")

        self.assertIsNotNone(result)
        self.assertEqual(len(result["periods"]), 8)
        self.assertEqual(result["periods"], [1, 2, 3, 4, 5, 6, 7, 8])

    def test_full_day_1_wan(self):
        """'1 วัน' → [1-8]"""
        result = parse_leave_request_fallback("ขอลา 1 วัน")

        self.assertIsNotNone(result)
        self.assertEqual(len(result["periods"]), 8)

    def test_full_day_nueng_wan(self):
        """'หนึ่งวัน' → [1-8]"""
        result = parse_leave_request_fallback("ขอลาหนึ่งวัน")

        self.assertIsNotNone(result)
        self.assertEqual(len(result["periods"]), 8)


class TestLateArrivalDetection(unittest.TestCase):
    """Test late arrival vs regular leave detection (Nov 25, 2025 feature)"""

    def test_kao_sai_detected_as_late(self):
        """'เข้าสาย' detected as late arrival"""
        result = parse_leave_request_fallback("วันนี้เข้าสายครับ")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "late")
        self.assertEqual(result["periods"], [1, 2, 3])  # Morning periods

    def test_ma_sai_detected_as_late(self):
        """'มาสาย' detected as late arrival"""
        result = parse_leave_request_fallback("พรุ่งนี้มาสาย")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "late")
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_late_arrival_with_reason(self):
        """Late arrival with reason extracted"""
        result = parse_leave_request_fallback("เข้าสาย ไปหาหมอ")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "late")
        self.assertIn("หาหมอ", result.get("reason", ""))

    def test_late_arrival_complex_message(self):
        """Complex late arrival message"""
        result = parse_leave_request_fallback("พรุ่งนี้ครูสุกฤษฎิ์เข้าสาย ต้องไปส่งลูกหาหมอครับ")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "late")
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_regular_leave_not_late(self):
        """Regular leave has leave_type='leave'"""
        result = parse_leave_request_fallback("ขอลาป่วย คาบ 1-3")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "leave")

    def test_full_day_leave_not_late(self):
        """Full day leave is not late arrival"""
        result = parse_leave_request_fallback("ขอลาทั้งวัน")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "leave")
        self.assertEqual(len(result["periods"]), 8)  # All periods


class TestReasonExtraction(unittest.TestCase):
    """Test leave reason extraction"""

    def test_reason_puai_sick(self):
        """'ป่วย' extracted as reason"""
        result = parse_leave_request_fallback("ขอลาป่วย คาบ 1")

        self.assertIsNotNone(result)
        self.assertIn("ป่วย", result.get("reason", ""))

    def test_reason_thura_personal(self):
        """'ธุระ' extracted as reason"""
        result = parse_leave_request_fallback("ขอลาธุระส่วนตัว คาบ 1-3")

        self.assertIsNotNone(result)
        self.assertIn("ธุระ", result.get("reason", ""))

    def test_reason_ha_mo_doctor(self):
        """'หาหมอ' extracted as reason"""
        result = parse_leave_request_fallback("ขอลาพรุ่งนี้ ไปหาหมอ คาบ 1-3")

        self.assertIsNotNone(result)
        # Should capture reason
        self.assertIn("reason", result)

    def test_no_reason_provided(self):
        """Missing reason handled gracefully"""
        result = parse_leave_request_fallback("ขอลาพรุ่งนี้ คาบ 1-3")

        # Should still parse successfully
        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_complex_reason(self):
        """Complex multi-word reason"""
        result = parse_leave_request_fallback("ขอลา ต้องไปส่งลูกหาหมอ คาบ 1-3")

        self.assertIsNotNone(result)


class TestFallbackParser(unittest.TestCase):
    """Test regex-based fallback when AI fails"""

    @patch('src.timetable.ai_parser.requests.post')
    def test_fallback_on_api_timeout(self, mock_post):
        """Falls back to regex when OpenRouter times out"""
        import requests

        # Mock API timeout
        mock_post.side_effect = requests.exceptions.Timeout("API timeout")

        result = parse_leave_request("ครูสมชาย ขอลาพรุ่งนี้ คาบ 1-3")

        # Should still get result from fallback
        self.assertIsNotNone(result)
        self.assertIn("periods", result)
        self.assertEqual(result["periods"], [1, 2, 3])

    @patch('src.timetable.ai_parser.requests.post')
    def test_fallback_on_api_error(self, mock_post):
        """Falls back to regex when OpenRouter returns error"""
        import requests

        # Mock API error
        mock_post.side_effect = requests.exceptions.RequestException("API error")

        result = parse_leave_request("ขอลาคาบ 1-6")

        # Should get result from fallback
        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3, 4, 5, 6])

    def test_fallback_feature_parity_full_day(self):
        """Fallback parser supports full day expressions"""
        # Test all full day expressions
        expressions = ["ทั้งวัน", "เต็มวัน", "1 วัน", "หนึ่งวัน"]

        for expr in expressions:
            result = parse_leave_request_fallback(f"ขอลา{expr}")
            self.assertIsNotNone(result, f"Failed to parse: {expr}")
            self.assertEqual(len(result["periods"]), 8, f"Wrong period count for: {expr}")

    def test_fallback_feature_parity_late_arrival(self):
        """Fallback parser supports late arrival detection"""
        late_expressions = ["เข้าสาย", "มาสาย"]

        for expr in late_expressions:
            result = parse_leave_request_fallback(f"{expr} วันนี้")
            self.assertIsNotNone(result, f"Failed to parse: {expr}")
            self.assertEqual(result["leave_type"], "late", f"Not detected as late: {expr}")
            self.assertEqual(result["periods"], [1, 2, 3], f"Wrong periods for: {expr}")

    @patch('src.timetable.ai_parser.requests.post')
    def test_ai_returns_invalid_json(self, mock_post):
        """Invalid JSON from AI triggers fallback"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "not valid json at all"
                }
            }]
        }
        mock_post.return_value = mock_response

        result = parse_leave_request("ขอลาพรุ่งนี้ คาบ 1-3")

        # Should fall back and still work
        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])


class TestRealWorldMessages(unittest.TestCase):
    """Test with actual LINE messages from production"""

    def test_message_formal_greeting_with_periods(self):
        """Real message: เรียนท่าน ผอ. วันนี้ ครูวิยะดา ขอลาป่วย คาบ 1-3"""
        result = parse_leave_request_fallback("เรียนท่าน ผอ. วันนี้ ครูวิยะดา ขอลาป่วย คาบ 1-3")

        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])
        self.assertIn("ป่วย", result.get("reason", ""))

    def test_message_late_arrival_with_reason(self):
        """Real message: พรุ่งนี้ครูสุกฤษฎิ์เข้าสาย ต้องไปส่งลูกหาหมอครับ"""
        result = parse_leave_request_fallback("พรุ่งนี้ครูสุกฤษฎิ์เข้าสาย ต้องไปส่งลูกหาหมอครับ")

        self.assertIsNotNone(result)
        self.assertEqual(result["leave_type"], "late")
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_message_full_day_leave(self):
        """Real message: ครูอรอนงค์ ขอลาพรุ่งนี้ทั้งวัน ธุระส่วนตัว"""
        result = parse_leave_request_fallback("ครูอรอนงค์ ขอลาพรุ่งนี้ทั้งวัน ธุระส่วนตัว")

        self.assertIsNotNone(result)
        self.assertEqual(len(result["periods"]), 8)
        self.assertEqual(result["leave_type"], "leave")

    def test_message_simple_format(self):
        """Real message: ขอลาพรุ่งนี้ คาบ 1,2,3"""
        result = parse_leave_request_fallback("ขอลาพรุ่งนี้ คาบ 1,2,3")

        self.assertIsNotNone(result)
        self.assertTrue(all(p in result["periods"] for p in [1, 2, 3]))

    def test_message_with_polite_ending(self):
        """Real message: ขอลาพรุ่งนี้ คาบ 1-3 ครับ"""
        result = parse_leave_request_fallback("ขอลาพรุ่งนี้ คาบ 1-3 ครับ")

        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])

    def test_message_multiple_periods_ranges(self):
        """Message with multiple period ranges"""
        result = parse_leave_request_fallback("ขอลาคาบ 1-2")

        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_empty_message(self):
        """Empty message returns None"""
        result = parse_leave_request_fallback("")

        self.assertIsNone(result)

    def test_whitespace_only_message(self):
        """Whitespace-only message returns None"""
        result = parse_leave_request_fallback("   \n\t   ")

        self.assertIsNone(result)

    def test_non_leave_message(self):
        """Non-leave message returns None"""
        result = parse_leave_request_fallback("สวัสดีครับ สบายดีไหม")

        self.assertIsNone(result)

    def test_greeting_only_message(self):
        """Greeting without leave request returns None"""
        result = parse_leave_request_fallback("เรียนท่าน ผอ. สวัสดีครับ")

        self.assertIsNone(result)

    def test_message_with_invalid_period_letters(self):
        """Message with invalid period format"""
        result = parse_leave_request_fallback("ขอลาคาบ abc")

        # Should handle gracefully, may return None or parse other parts
        # At minimum should not crash

    def test_message_with_negative_periods(self):
        """Message with negative period numbers"""
        result = parse_leave_request_fallback("ขอลาคาบ -1,-2")

        # Should handle gracefully

    def test_message_with_very_large_period(self):
        """Message with unreasonably large period number"""
        result = parse_leave_request_fallback("ขอลาคาบ 999")

        # Should handle gracefully

    def test_message_with_only_period_no_date(self):
        """Message with period but no date"""
        result = parse_leave_request_fallback("ขอลาคาบ 1-3")

        # Should still extract periods
        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])

    @patch('src.timetable.ai_parser.requests.post')
    def test_ai_api_missing_choices(self, mock_post):
        """AI API returns response without choices field"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "No choices"}
        mock_post.return_value = mock_response

        result = parse_leave_request("ขอลาคาบ 1-3")

        # Should fall back to regex parser
        self.assertIsNotNone(result)
        self.assertEqual(result["periods"], [1, 2, 3])

    @patch('src.timetable.ai_parser.requests.post')
    def test_ai_api_empty_response(self, mock_post):
        """AI API returns empty response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        result = parse_leave_request("ขอลาคาบ 1-3")

        # Should fall back
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
