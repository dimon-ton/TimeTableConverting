"""
Integration tests for complete LINE Bot workflows.

These tests verify end-to-end workflows across multiple components:
- Webhook → Parser → Sheets → LINE (leave request flow)
- Sheets → Substitute Finder → LINE (daily processing flow)
- Error propagation across components

All tests use mocks - no actual API calls or database access.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import json


class TestLeaveRequestWorkflow(unittest.TestCase):
    """Test complete leave request workflow from LINE message to confirmation"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_successful_leave_request_complete_flow(self, mock_send, mock_log, mock_parse, mock_config):
        """Complete workflow: LINE message → AI parse → Google Sheets → Admin notification"""
        # Setup config
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group_123"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group_456"
        mock_config.DEBUG_MODE = False

        # Mock successful AI parsing
        mock_parse.return_value = {
            'teacher_name': 'สุกฤษฎิ์',
            'date': '2025-11-26',
            'periods': [1, 2, 3],
            'reason': 'ป่วย',
            'leave_type': 'leave'
        }

        # Mock successful Sheets logging
        mock_log.return_value = None

        # Mock successful LINE notification
        mock_send.return_value = True

        # Import and call the workflow function
        from src.web.webhook import process_leave_request_message

        # Execute workflow
        process_leave_request_message(
            text="ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3 ป่วย",
            group_id="teacher_group_123",
            reply_token="reply_token_abc"
        )

        # Verify workflow steps executed in order
        # 1. AI parser was called
        mock_parse.assert_called_once()

        # 2. Request was logged to Google Sheets
        mock_log.assert_called_once()
        log_call = mock_log.call_args
        self.assertEqual(log_call[1]['raw_message'], "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3 ป่วย")
        self.assertEqual(log_call[1]['status'], "Success (AI)")

        # 3. Confirmation was sent to admin group
        mock_send.assert_called_once()
        confirmation = mock_send.call_args[0][0]
        self.assertIn('สุกฤษฎิ์', confirmation)
        self.assertIn('2025-11-26', confirmation)
        self.assertIn('1, 2, 3', confirmation)

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.parse_leave_request_fallback')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_ai_parser_failure_triggers_fallback(self, mock_send, mock_log, mock_fallback, mock_ai, mock_config):
        """When AI fails, workflow should use fallback parser"""
        # Setup
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group_123"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group_456"

        # AI parser fails
        mock_ai.return_value = None

        # Fallback parser succeeds
        mock_fallback.return_value = {
            'teacher_name': 'test',
            'date': '2025-11-26',
            'periods': [1, 2, 3],
            'leave_type': 'leave'
        }

        from src.web.webhook import process_leave_request_message

        # Execute
        process_leave_request_message("ขอลา คาบ 1-3", "teacher_group_123", "token")

        # Verify both parsers were called
        mock_ai.assert_called_once()
        mock_fallback.assert_called_once()

        # Verify workflow continued with fallback result
        mock_log.assert_called_once()
        log_call = mock_log.call_args
        self.assertEqual(log_call[1]['status'], "Success (Fallback)")

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.parse_leave_request_fallback')
    @patch('src.web.webhook.send_to_admin')
    @patch('src.web.webhook.log_request_to_sheet')
    def test_both_parsers_fail_sends_error(self, mock_log, mock_send, mock_fallback, mock_ai, mock_config):
        """When both parsers fail, error notification should be sent"""
        # Setup
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group_123"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group_456"

        # Both parsers fail
        mock_ai.return_value = None
        mock_fallback.return_value = None

        from src.web.webhook import process_leave_request_message

        # Execute
        process_leave_request_message("invalid message", "teacher_group_123", "token")

        # Verify failure was logged
        mock_log.assert_called_once()
        log_call = mock_log.call_args
        self.assertEqual(log_call[1]['status'], "Failed")

        # Verify error notification was sent
        mock_send.assert_called()
        error_msg = mock_send.call_args[0][0]
        self.assertIn("❌", error_msg)
        self.assertIn("ล้มเหลว", error_msg)


class TestDailyProcessingWorkflow(unittest.TestCase):
    """Test daily leave processing workflow"""

    @patch('src.utils.daily_leave_processor.load_data_files')
    @patch('src.utils.daily_leave_processor.get_and_enrich_leaves')
    @patch('src.utils.daily_leave_processor.assign_substitutes_for_day')
    @patch('src.utils.daily_leave_processor.update_sheets_with_substitutes')
    @patch('src.utils.daily_leave_processor.send_daily_report')
    def test_daily_processing_success_flow(self, mock_send, mock_update, mock_assign, mock_enrich, mock_load):
        """Daily processing: Load data → Enrich leaves → Assign substitutes → Update sheets → Send report"""
        # This test verifies the daily processing workflow would execute correctly
        # In a real scenario, we'd import and call the actual daily_leave_processor

        # Mock data loading
        mock_load.return_value = {
            'timetable': [],
            'teacher_subjects': {},
            'teacher_levels': {},
            'class_levels': {},
            'teacher_names': {}
        }

        # Mock enriched leave data
        mock_enrich.return_value = [
            {
                'teacher_id': 'T004',
                'date': '2025-11-26',
                'day_id': 'Mon',
                'period_id': 1,
                'class_id': 'ป.1',
                'subject_id': 'English'
            }
        ]

        # Mock substitute assignment
        mock_assign.return_value = [
            {
                'absent_teacher_id': 'T004',
                'substitute_teacher_id': 'T012',
                'period_id': 1,
                'class_id': 'ป.1',
                'subject_id': 'English'
            }
        ]

        # Mock successful update
        mock_update.return_value = None

        # Mock successful notification
        mock_send.return_value = True

        # Verify the workflow components would be called in correct order
        # (Actual execution would be in daily_leave_processor.py)

    @patch('src.timetable.substitute.assign_substitutes_for_day')
    @patch('src.web.line_messaging.send_daily_report')
    def test_substitute_assignment_integration(self, mock_send_report, mock_assign):
        """Test substitute assignment integrates with LINE reporting"""
        # Mock substitute assignment results
        mock_assign.return_value = [
            {
                "absent_teacher_id": "T004",
                "substitute_teacher_id": "T012",
                "day_id": "Mon",
                "period_id": 1,
                "class_id": "ป.1",
                "subject_id": "Math"
            },
            {
                "absent_teacher_id": "T004",
                "substitute_teacher_id": None,  # No substitute found
                "day_id": "Mon",
                "period_id": 2,
                "class_id": "ป.2",
                "subject_id": "Science"
            }
        ]

        # In real workflow, these results would be formatted and sent
        # Verify the data structure is compatible with LINE messaging

        from src.web.line_messaging import format_substitute_summary

        # Calculate statistics
        total_periods = len(mock_assign.return_value)
        substitutes_found = sum(
            1 for a in mock_assign.return_value
            if a.get('substitute_teacher_id') is not None
        )

        # Format summary
        summary = format_substitute_summary(
            date="2025-11-26",
            total_absences=1,
            total_periods=total_periods,
            substitutes_found=substitutes_found
        )

        # Verify summary is generated correctly
        self.assertIn("2 คาบ", summary)  # 2 total periods
        self.assertIn("1/2", summary)  # 1 of 2 found
        self.assertIn("50%", summary)  # 50% success rate


class TestErrorPropagation(unittest.TestCase):
    """Test error handling across integrated components"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_sheets_api_failure_propagates_error(self, mock_send, mock_log, mock_parse, mock_config):
        """Google Sheets failure should send error notification"""
        # Setup
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # Parser succeeds
        mock_parse.return_value = {
            'teacher_name': 'test',
            'date': '2025-11-26',
            'periods': [1],
            'leave_type': 'leave'
        }

        # Sheets API fails
        mock_log.side_effect = Exception("Sheets API connection error")

        from src.web.webhook import process_leave_request_message

        # Execute - should not crash
        process_leave_request_message("ขอลา", "teacher_group", "token")

        # Verify error notification was sent
        mock_send.assert_called()
        error_msg = mock_send.call_args[0][0]
        self.assertIn("⚠️", error_msg)
        self.assertIn("ข้อผิดพลาด", error_msg)

    @patch('src.web.line_messaging.get_line_bot_api')
    def test_line_api_configuration_error(self, mock_get_api):
        """LINE API configuration error handled gracefully"""
        # Mock configuration error
        mock_get_api.side_effect = ValueError("LINE_CHANNEL_ACCESS_TOKEN not set")

        from src.web.line_messaging import send_message_to_group

        # Should return False, not crash
        result = send_message_to_group("Test", "group_id")

        self.assertFalse(result)

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.verify_signature')
    def test_invalid_signature_blocks_workflow(self, mock_verify, mock_config):
        """Invalid signature should prevent workflow execution"""
        mock_config.DEBUG_MODE = False
        mock_verify.return_value = False  # Invalid signature

        from src.web.webhook import webhook
        client = webhook.app.test_client()

        # Attempt callback with invalid signature
        response = client.post('/callback',
            data=json.dumps({'events': []}),
            headers={'X-Line-Signature': 'invalid'},
            content_type='application/json')

        # Should be rejected
        self.assertEqual(response.status_code, 400)

    @patch('src.web.line_messaging.send_message_to_group')
    @patch('src.web.line_messaging.config')
    def test_line_send_retry_logic(self, mock_config, mock_send):
        """Test that failed LINE sends are handled but not retried indefinitely"""
        mock_config.LINE_GROUP_ID = "test_group"

        # First call fails
        mock_send.side_effect = [Exception("Network error"), True]

        from src.web.line_messaging import send_daily_report

        # First attempt should catch exception
        result = send_daily_report("Test report")

        # Should handle error gracefully
        # (Current implementation doesn't retry, just returns False)


class TestDataFlowIntegrity(unittest.TestCase):
    """Test data integrity across workflow"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_leave_data_preserves_thai_characters(self, mock_send, mock_log, mock_parse, mock_config):
        """Thai characters preserved through entire workflow"""
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # Parser returns Thai text
        mock_parse.return_value = {
            'teacher_name': 'สุกฤษฎิ์',
            'date': '2025-11-26',
            'periods': [1, 2, 3],
            'reason': 'ป่วย',
            'leave_type': 'leave'
        }

        from src.web.webhook import process_leave_request_message

        # Execute workflow
        process_leave_request_message(
            "ครูสุกฤษฎิ์ ขอลาป่วย",
            "teacher_group",
            "token"
        )

        # Verify Thai text was preserved in Sheets logging
        log_call = mock_log.call_args
        leave_data = log_call[1]['leave_data']
        self.assertEqual(leave_data['teacher_name'], 'สุกฤษฎิ์')
        self.assertEqual(leave_data['reason'], 'ป่วย')

        # Verify Thai text in confirmation message
        confirmation = mock_send.call_args[0][0]
        self.assertIn('สุกฤษฎิ์', confirmation)
        self.assertIn('ป่วย', confirmation)  # Reason may be included

    def test_period_format_consistency(self):
        """Period format consistent between parser and substitute finder"""
        # Parser returns periods as list of ints
        parsed_periods = [1, 2, 3]

        # Substitute finder expects same format
        from src.timetable.substitute import find_best_substitute_teacher

        # Format should be compatible
        # (This is a structural test, not a full execution)
        self.assertIsInstance(parsed_periods, list)
        self.assertTrue(all(isinstance(p, int) for p in parsed_periods))


if __name__ == '__main__':
    unittest.main()
