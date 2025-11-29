"""
Comprehensive tests for LINE messaging functions.

Tests cover:
- Message sending to groups
- Two-group architecture (teacher/admin routing)
- Report formatting
- Error notifications
- Thai text handling
- API failure scenarios

All tests use mocks - no actual LINE API calls.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock

from src.web import line_messaging


class TestMessageSending(unittest.TestCase):
    """Test LINE message sending functionality"""

    @patch('src.web.line_messaging.get_line_bot_api')
    @patch('src.web.line_messaging.config')
    def test_send_message_to_group_success(self, mock_config, mock_get_api):
        """Message sent to group successfully"""
        # Setup mocks
        mock_config.LINE_GROUP_ID = "test_group_123"
        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        # Send message
        result = line_messaging.send_message_to_group("Test message")

        # Verify API was called
        mock_api.push_message.assert_called_once()

        # Verify success
        self.assertTrue(result)

    @patch('src.web.line_messaging.get_line_bot_api')
    @patch('src.web.line_messaging.config')
    def test_send_message_to_admin_group(self, mock_config, mock_get_api):
        """Message sent to admin group successfully"""
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group_456"
        mock_config.LINE_GROUP_ID = "fallback_group"
        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        result = line_messaging.send_to_admin_group("Admin message")

        # Verify success
        self.assertTrue(result)

        # Verify correct group ID used
        call_args = mock_api.push_message.call_args
        push_request = call_args[0][0]
        self.assertEqual(push_request.to, "admin_group_456")

    @patch('src.web.line_messaging.get_line_bot_api')
    @patch('src.web.line_messaging.config')
    def test_send_message_to_teacher_group(self, mock_config, mock_get_api):
        """Message sent to teacher group successfully"""
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group_789"
        mock_config.LINE_GROUP_ID = "fallback_group"
        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        result = line_messaging.send_to_teacher_group("Teacher message")

        # Verify success
        self.assertTrue(result)

        # Verify correct group ID
        call_args = mock_api.push_message.call_args
        push_request = call_args[0][0]
        self.assertEqual(push_request.to, "teacher_group_789")

    @patch('src.web.line_messaging.config')
    def test_send_message_no_group_id(self, mock_config):
        """Sending without group ID should fail"""
        mock_config.LINE_GROUP_ID = None

        result = line_messaging.send_message_to_group("Test message")

        # Should fail
        self.assertFalse(result)

    @patch('src.web.line_messaging.get_line_bot_api')
    @patch('src.web.line_messaging.config')
    def test_send_message_api_failure(self, mock_config, mock_get_api):
        """API failure should be handled gracefully"""
        mock_config.LINE_GROUP_ID = "test_group"
        mock_api = MagicMock()
        mock_api.push_message.side_effect = Exception("API Error")
        mock_get_api.return_value = mock_api

        result = line_messaging.send_message_to_group("Test message")

        # Should fail gracefully
        self.assertFalse(result)

    @patch('src.web.line_messaging.config')
    def test_get_line_bot_api_no_token(self, mock_config):
        """get_line_bot_api should raise error without token"""
        mock_config.LINE_CHANNEL_ACCESS_TOKEN = None

        with self.assertRaises(ValueError):
            line_messaging.get_line_bot_api()


class TestGroupRouting(unittest.TestCase):
    """Test two-group architecture routing"""

    @patch('src.web.line_messaging.send_message_to_group')
    @patch('src.web.line_messaging.config')
    def test_admin_group_fallback_to_legacy(self, mock_config, mock_send):
        """Admin group falls back to LINE_GROUP_ID if ADMIN_GROUP not set"""
        mock_config.LINE_ADMIN_GROUP_ID = None
        mock_config.LINE_GROUP_ID = "legacy_group"
        mock_send.return_value = True

        line_messaging.send_to_admin_group("Test message")

        # Verify fallback was used
        mock_send.assert_called_once_with("Test message", "legacy_group")

    @patch('src.web.line_messaging.send_message_to_group')
    @patch('src.web.line_messaging.config')
    def test_teacher_group_fallback_to_legacy(self, mock_config, mock_send):
        """Teacher group falls back to LINE_GROUP_ID if TEACHER_GROUP not set"""
        mock_config.LINE_TEACHER_GROUP_ID = None
        mock_config.LINE_GROUP_ID = "legacy_group"
        mock_send.return_value = True

        line_messaging.send_to_teacher_group("Test message")

        # Verify fallback was used
        mock_send.assert_called_once_with("Test message", "legacy_group")

    @patch('src.web.line_messaging.config')
    def test_admin_group_no_config(self, mock_config):
        """Admin group with no config should fail"""
        mock_config.LINE_ADMIN_GROUP_ID = None
        mock_config.LINE_GROUP_ID = None

        result = line_messaging.send_to_admin_group("Test")

        self.assertFalse(result)

    @patch('src.web.line_messaging.config')
    def test_teacher_group_no_config(self, mock_config):
        """Teacher group with no config should fail"""
        mock_config.LINE_TEACHER_GROUP_ID = None
        mock_config.LINE_GROUP_ID = None

        result = line_messaging.send_to_teacher_group("Test")

        self.assertFalse(result)


class TestReportFormatting(unittest.TestCase):
    """Test daily substitute report formatting"""

    def test_format_substitute_summary_100_percent(self):
        """Summary with 100% success rate"""
        summary = line_messaging.format_substitute_summary(
            date="2025-11-26",
            total_absences=2,
            total_periods=10,
            substitutes_found=10
        )

        # Verify components
        self.assertIn("2025-11-26", summary)
        self.assertIn("2 คน", summary)  # 2 teachers absent
        self.assertIn("10 คาบ", summary)  # 10 periods
        self.assertIn("10/10", summary)  # All found
        self.assertIn("100%", summary)  # 100% success
        self.assertNotIn("⚠️", summary)  # No warning

    def test_format_substitute_summary_partial_success(self):
        """Summary with partial success"""
        summary = line_messaging.format_substitute_summary(
            date="2025-11-26",
            total_absences=3,
            total_periods=12,
            substitutes_found=8
        )

        # Verify components
        self.assertIn("8/12", summary)
        self.assertIn("67%", summary)  # 8/12 = 66.67%
        self.assertIn("⚠️", summary)  # Warning for missing
        self.assertIn("4 คาบ", summary)  # 4 missing

    def test_format_substitute_summary_zero_periods(self):
        """Summary with no periods (edge case)"""
        summary = line_messaging.format_substitute_summary(
            date="2025-11-26",
            total_absences=0,
            total_periods=0,
            substitutes_found=0
        )

        # Should not crash
        self.assertIsNotNone(summary)
        self.assertIn("0 คน", summary)

    def test_format_detailed_assignment_with_substitute(self):
        """Format assignment with substitute found"""
        formatted = line_messaging.format_detailed_assignment(
            day="Mon",
            period=3,
            class_id="ป.1",
            subject="Math",
            absent_teacher="T004",
            substitute_teacher="T012"
        )

        # Verify format
        self.assertIn("Mon", formatted)
        self.assertIn("คาบ 3", formatted)
        self.assertIn("ป.1", formatted)
        self.assertIn("Math", formatted)
        self.assertIn("T004", formatted)
        self.assertIn("T012", formatted)
        self.assertIn("→", formatted)

    def test_format_detailed_assignment_no_substitute(self):
        """Format assignment without substitute"""
        formatted = line_messaging.format_detailed_assignment(
            day="Mon",
            period=3,
            class_id="ป.1",
            subject="Math",
            absent_teacher="T004",
            substitute_teacher=None
        )

        # Verify format
        self.assertIn("ไม่มีครูแทน", formatted)
        self.assertIn("❌", formatted)


class TestSpecializedMessages(unittest.TestCase):
    """Test specialized message types"""

    @patch('src.web.line_messaging.send_to_admin_group')
    def test_send_daily_report_adds_header(self, mock_send):
        """Daily report should add header emoji"""
        mock_send.return_value = True

        result = line_messaging.send_daily_report("Report content here")

        # Verify header was added
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        self.assertIn("📋", args)
        self.assertIn("รายงานครูแทน", args)
        self.assertIn("Report content here", args)

    @patch('src.web.line_messaging.send_to_admin_group')
    def test_send_error_notification_adds_warning(self, mock_send):
        """Error notification should add warning emoji"""
        mock_send.return_value = True

        result = line_messaging.send_error_notification("Something went wrong")

        # Verify warning was added
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        self.assertIn("⚠️", args)
        self.assertIn("ข้อผิดพลาด", args)
        self.assertIn("Something went wrong", args)

    @patch('src.web.line_messaging.send_message_to_group')
    @patch('src.web.line_messaging.config')
    def test_send_test_message_format(self, mock_config, mock_send):
        """Test message should have proper format"""
        mock_config.DAILY_PROCESS_TIME = "08:55"
        mock_send.return_value = True

        result = line_messaging.send_test_message()

        # Verify test message format
        mock_send.assert_called_once()
        args = mock_send.call_args[0][0]
        self.assertIn("🧪", args)
        self.assertIn("ทดสอบระบบ", args)
        self.assertIn("08:55", args)
        self.assertIn("✓", args)


class TestThaiTextHandling(unittest.TestCase):
    """Test Thai message formatting and emojis"""

    def test_thai_unicode_preserved_in_summary(self):
        """Thai characters preserved in summary"""
        summary = line_messaging.format_substitute_summary(
            date="2025-11-26",
            total_absences=1,
            total_periods=5,
            substitutes_found=5
        )

        # Thai text should be intact
        self.assertIn("ครูที่ลา", summary)
        self.assertIn("คน", summary)
        self.assertIn("คาบ", summary)

    def test_emoji_in_formatted_messages(self):
        """Emojis included in formatted messages"""
        summary = line_messaging.format_substitute_summary(
            date="2025-11-26",
            total_absences=1,
            total_periods=5,
            substitutes_found=3
        )

        # Check for emojis
        self.assertIn("📅", summary)
        self.assertIn("👥", summary)
        self.assertIn("📚", summary)
        self.assertIn("✅", summary)
        self.assertIn("⚠️", summary)  # Warning for incomplete

    @patch('src.web.line_messaging.send_to_admin_group')
    def test_thai_text_in_reports(self, mock_send):
        """Thai text handled correctly in reports"""
        mock_send.return_value = True

        line_messaging.send_daily_report("ครูแทน: T001 → T002")

        args = mock_send.call_args[0][0]
        self.assertIn("ครูแทน", args)


class TestFormattedReportGeneration(unittest.TestCase):
    """Test comprehensive formatted report generation"""

    @patch('src.web.line_messaging.send_message_to_group')
    @patch('src.web.line_messaging.config')
    def test_send_formatted_report_structure(self, mock_config, mock_send):
        """Formatted report has correct structure"""
        mock_config.LINE_GROUP_ID = "test_group"
        mock_send.return_value = True

        # Sample data
        absent_teachers = [
            {"teacher_id": "T004", "name": "ครูสุกฤษฎิ์"},
            {"teacher_id": "T002", "name": "ครูสมชาย"}
        ]

        assignments = [
            {
                "day_id": "Mon",
                "period_id": 1,
                "class_id": "ป.1",
                "subject_id": "Math",
                "teacher_id": "T004",
                "substitute_teacher": "T012"
            },
            {
                "day_id": "Mon",
                "period_id": 2,
                "class_id": "ป.2",
                "subject_id": "Science",
                "teacher_id": "T002",
                "substitute_teacher": None
            }
        ]

        result = line_messaging.send_formatted_report(
            date="2025-11-26",
            absent_teachers=absent_teachers,
            assignments=assignments
        )

        # Verify success
        self.assertTrue(result)

        # Verify message structure
        mock_send.assert_called_once()
        message = mock_send.call_args[0][0]

        # Check header
        self.assertIn("📋", message)
        self.assertIn("รายงานครูแทนประจำวัน", message)
        self.assertIn("2025-11-26", message)

        # Check summary
        self.assertIn("2 คน", message)  # 2 unique teachers
        self.assertIn("2 คาบ", message)  # 2 periods
        self.assertIn("1/2", message)  # 1 of 2 substitutes found

        # Check assignments
        self.assertIn("Mon", message)
        self.assertIn("ป.1", message)
        self.assertIn("ป.2", message)
        self.assertIn("T012", message)  # Substitute
        self.assertIn("ไม่มีครูแทน", message)  # No substitute for 2nd

    @patch('src.web.line_messaging.send_message_to_group')
    @patch('src.web.line_messaging.config')
    def test_formatted_report_empty_assignments(self, mock_config, mock_send):
        """Formatted report with no assignments"""
        mock_config.LINE_GROUP_ID = "test_group"
        mock_send.return_value = True

        result = line_messaging.send_formatted_report(
            date="2025-11-26",
            absent_teachers=[],
            assignments=[]
        )

        # Should not crash
        self.assertTrue(result)

        message = mock_send.call_args[0][0]
        self.assertIn("0 คน", message)
        self.assertIn("0 คาบ", message)


if __name__ == '__main__':
    unittest.main()
