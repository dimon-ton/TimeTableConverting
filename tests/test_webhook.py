"""
Comprehensive tests for LINE Bot webhook server.

Tests cover:
- Signature verification (security)
- Message event handling
- Leave keyword detection
- Error handling
- Health endpoints
- Group filtering

All tests use mocks - no actual LINE API calls or Google Sheets access.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import hashlib
import hmac
import base64

# Import the Flask app
from src.web import webhook


class TestSignatureVerification(unittest.TestCase):
    """Test LINE signature verification security"""

    def test_valid_signature_accepted(self):
        """Valid HMAC-SHA256 signature should pass verification"""
        # Setup test data
        test_body = b"test webhook body"
        secret = "test_secret_key"

        # Generate valid signature
        hash_digest = hmac.new(
            secret.encode('utf-8'),
            test_body,
            hashlib.sha256
        ).digest()
        valid_signature = base64.b64encode(hash_digest).decode('utf-8')

        # Mock config
        with patch('src.web.webhook.config') as mock_config:
            mock_config.LINE_CHANNEL_SECRET = secret
            mock_config.DEBUG_MODE = False

            # Test verification
            result = webhook.verify_signature(test_body, valid_signature)
            self.assertTrue(result, "Valid signature should be accepted")

    def test_invalid_signature_rejected(self):
        """Invalid signature should be rejected"""
        test_body = b"test webhook body"
        secret = "test_secret_key"
        invalid_signature = "invalid_signature_value"

        with patch('src.web.webhook.config') as mock_config:
            mock_config.LINE_CHANNEL_SECRET = secret
            mock_config.DEBUG_MODE = False

            result = webhook.verify_signature(test_body, invalid_signature)
            self.assertFalse(result, "Invalid signature should be rejected")

    def test_missing_secret_in_debug_mode(self):
        """Missing secret in debug mode should allow request"""
        test_body = b"test body"
        signature = "any_signature"

        with patch('src.web.webhook.config') as mock_config:
            mock_config.LINE_CHANNEL_SECRET = None
            mock_config.DEBUG_MODE = True

            result = webhook.verify_signature(test_body, signature)
            self.assertTrue(result, "Debug mode should allow requests without secret")

    def test_missing_secret_not_in_debug_mode(self):
        """Missing secret not in debug mode should reject"""
        test_body = b"test body"
        signature = "any_signature"

        with patch('src.web.webhook.config') as mock_config:
            mock_config.LINE_CHANNEL_SECRET = None
            mock_config.DEBUG_MODE = False

            result = webhook.verify_signature(test_body, signature)
            self.assertFalse(result, "Without secret and not debug, should reject")


class TestCallbackEndpoint(unittest.TestCase):
    """Test /callback webhook endpoint"""

    def setUp(self):
        """Set up Flask test client"""
        webhook.app.config['TESTING'] = True
        self.client = webhook.app.test_client()

    @patch('src.web.webhook.handler')
    @patch('src.web.webhook.verify_signature')
    def test_valid_request_returns_ok(self, mock_verify, mock_handler):
        """Valid webhook request should return OK"""
        # Setup mocks
        mock_verify.return_value = True
        mock_handler.handle.return_value = None

        # Make request
        response = self.client.post('/callback',
            data=json.dumps({'events': []}),
            headers={'X-Line-Signature': 'test_sig'},
            content_type='application/json')

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'OK')

    @patch('src.web.webhook.verify_signature')
    def test_invalid_signature_returns_400(self, mock_verify):
        """Invalid signature should return 400"""
        # Setup mock to reject signature
        mock_verify.return_value = False

        # Make request
        response = self.client.post('/callback',
            data=json.dumps({'events': []}),
            headers={'X-Line-Signature': 'invalid_sig'},
            content_type='application/json')

        # Verify 400 error
        self.assertEqual(response.status_code, 400)

    @patch('src.web.webhook.verify_signature')
    def test_missing_signature_returns_400(self, mock_verify):
        """Missing X-Line-Signature header should return 400"""
        # Setup mock to reject (empty signature)
        mock_verify.return_value = False

        # Make request without signature header
        response = self.client.post('/callback',
            data=json.dumps({'events': []}),
            content_type='application/json')

        # Verify 400 error
        self.assertEqual(response.status_code, 400)

    @patch('src.web.webhook.handler')
    @patch('src.web.webhook.verify_signature')
    @patch('src.web.webhook.process_webhook_manually')
    def test_manual_processing_when_handler_none(self, mock_process, mock_verify, mock_handler):
        """Should use manual processing when handler is None"""
        mock_verify.return_value = True

        # Temporarily set handler to None
        original_handler = webhook.handler
        webhook.handler = None

        try:
            # Make request
            test_data = {'events': [{'type': 'message'}]}
            response = self.client.post('/callback',
                data=json.dumps(test_data),
                headers={'X-Line-Signature': 'test_sig'},
                content_type='application/json')

            # Verify manual processing was called
            mock_process.assert_called_once()
            self.assertEqual(response.status_code, 200)
        finally:
            # Restore handler
            webhook.handler = original_handler


class TestLeaveKeywordDetection(unittest.TestCase):
    """Test leave request keyword detection"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_keyword_la_detected(self, mock_send, mock_log, mock_parse, mock_config):
        """'ลา' keyword should trigger processing"""
        # Setup config
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_GROUP_ID = "test_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # Setup parser to return valid data
        mock_parse.return_value = {
            'teacher_name': 'สมชาย',
            'date': '2025-11-26',
            'periods': [1, 2, 3],
            'reason': 'ป่วย',
            'leave_type': 'leave'
        }

        # Process message with 'ลา'
        webhook.process_leave_request_message("ครูสมชาย ลาพรุ่งนี้", "test_group", "token123")

        # Verify parser was called
        mock_parse.assert_called_once()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_keyword_kho_la_detected(self, mock_parse, mock_config):
        """'ขอลา' keyword should trigger processing"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_GROUP_ID = "test_group"

        mock_parse.return_value = {'teacher_name': 'test', 'date': '2025-11-26', 'periods': [1]}

        webhook.process_leave_request_message("ขอลาคาบ 1-3", "test_group", "token")

        mock_parse.assert_called_once()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_keyword_yut_detected(self, mock_parse, mock_config):
        """'หยุด' keyword should trigger processing"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_GROUP_ID = "test_group"

        mock_parse.return_value = {'teacher_name': 'test', 'date': '2025-11-26', 'periods': [1]}

        webhook.process_leave_request_message("หยุดวันนี้", "test_group", "token")

        mock_parse.assert_called_once()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_keyword_mai_ma_detected(self, mock_parse, mock_config):
        """'ไม่มา' keyword should trigger processing"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_GROUP_ID = "test_group"

        mock_parse.return_value = {'teacher_name': 'test', 'date': '2025-11-26', 'periods': [1]}

        webhook.process_leave_request_message("ไม่มาสอน", "test_group", "token")

        mock_parse.assert_called_once()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_non_leave_message_ignored(self, mock_parse, mock_config):
        """Message without leave keywords should be ignored"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_GROUP_ID = "test_group"

        # Process non-leave message
        webhook.process_leave_request_message("สวัสดีครับ ผอ.", "test_group", "token")

        # Parser should NOT be called
        mock_parse.assert_not_called()


class TestGroupFiltering(unittest.TestCase):
    """Test message filtering by group ID"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_correct_group_accepted(self, mock_parse, mock_config):
        """Messages from teacher group should be processed"""
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group_123"
        mock_config.LINE_GROUP_ID = "fallback_group"

        mock_parse.return_value = {'teacher_name': 'test', 'date': '2025-11-26', 'periods': [1]}

        webhook.process_leave_request_message("ขอลา", "teacher_group_123", "token")

        # Should process
        mock_parse.assert_called_once()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_wrong_group_ignored(self, mock_parse, mock_config):
        """Messages from non-teacher groups should be ignored"""
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group_123"
        mock_config.LINE_GROUP_ID = None

        # Message from different group
        webhook.process_leave_request_message("ขอลา", "other_group_456", "token")

        # Should NOT process
        mock_parse.assert_not_called()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    def test_fallback_to_line_group_id(self, mock_parse, mock_config):
        """Should fallback to LINE_GROUP_ID if TEACHER_GROUP_ID not set"""
        mock_config.LINE_TEACHER_GROUP_ID = None
        mock_config.LINE_GROUP_ID = "fallback_group"

        mock_parse.return_value = {'teacher_name': 'test', 'date': '2025-11-26', 'periods': [1]}

        webhook.process_leave_request_message("ขอลา", "fallback_group", "token")

        # Should process using fallback
        mock_parse.assert_called_once()


class TestErrorHandling(unittest.TestCase):
    """Test webhook error handling"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.parse_leave_request_fallback')
    @patch('src.web.webhook.send_to_admin')
    def test_ai_parser_failure_uses_fallback(self, mock_send, mock_fallback, mock_ai, mock_config):
        """When AI parser fails, should try fallback parser"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # AI parser returns None (failure)
        mock_ai.return_value = None

        # Fallback parser succeeds
        mock_fallback.return_value = {
            'teacher_name': 'test',
            'date': '2025-11-26',
            'periods': [1, 2, 3]
        }

        with patch('src.web.webhook.log_request_to_sheet'):
            webhook.process_leave_request_message("ขอลา", "test_group", "token")

        # Both parsers should be called
        mock_ai.assert_called_once()
        mock_fallback.assert_called_once()

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.parse_leave_request_fallback')
    @patch('src.web.webhook.send_to_admin')
    @patch('src.web.webhook.log_request_to_sheet')
    def test_both_parsers_fail_sends_error(self, mock_log, mock_send, mock_fallback, mock_ai, mock_config):
        """When both parsers fail, should send error notification"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # Both parsers fail
        mock_ai.return_value = None
        mock_fallback.return_value = None

        webhook.process_leave_request_message("ขอลา invalid", "test_group", "token")

        # Should log failure
        mock_log.assert_called()
        args = mock_log.call_args
        self.assertEqual(args[1]['status'], "Failed")

        # Should send error to admin
        mock_send.assert_called()
        error_msg = mock_send.call_args[0][0]
        self.assertIn("❌", error_msg)
        self.assertIn("ล้มเหลว", error_msg)

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_sheets_failure_sends_error(self, mock_send, mock_log, mock_parse, mock_config):
        """Google Sheets failure should send error notification"""
        mock_config.LINE_TEACHER_GROUP_ID = "test_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # Parser succeeds
        mock_parse.return_value = {
            'teacher_name': 'test',
            'date': '2025-11-26',
            'periods': [1]
        }

        # Sheets API fails
        mock_log.side_effect = Exception("Sheets API error")

        webhook.process_leave_request_message("ขอลา", "test_group", "token")

        # Should send error notification
        mock_send.assert_called()
        error_msg = mock_send.call_args[0][0]
        self.assertIn("⚠️", error_msg)
        self.assertIn("ข้อผิดพลาด", error_msg)

    @patch('src.web.webhook.verify_signature')
    @patch('src.web.webhook.handler')
    def test_invalid_signature_error_caught(self, mock_handler, mock_verify):
        """InvalidSignatureError should be caught and return 400"""
        from linebot.v3.exceptions import InvalidSignatureError

        mock_verify.return_value = True
        mock_handler.handle.side_effect = InvalidSignatureError("Invalid")

        client = webhook.app.test_client()
        response = client.post('/callback',
            data=json.dumps({'events': []}),
            headers={'X-Line-Signature': 'sig'},
            content_type='application/json')

        # Should return 400
        self.assertEqual(response.status_code, 400)


class TestHealthEndpoints(unittest.TestCase):
    """Test health check endpoints"""

    def setUp(self):
        """Set up Flask test client"""
        webhook.app.config['TESTING'] = True
        self.client = webhook.app.test_client()

    def test_home_endpoint(self):
        """Home endpoint should return success message"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"running", response.data)

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.line_bot_api')
    @patch('src.web.webhook.handler')
    def test_health_endpoint_returns_status(self, mock_handler, mock_api, mock_config):
        """Health endpoint should return JSON status"""
        mock_config.SPREADSHEET_ID = "test_spreadsheet_id_1234567890"
        mock_api.__bool__ = Mock(return_value=True)
        mock_handler.__bool__ = Mock(return_value=True)

        response = self.client.get('/health')

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['status'], 'ok')
        self.assertIn('line_bot_api', data)
        self.assertIn('webhook_handler', data)

    @patch('src.web.webhook.config')
    def test_health_endpoint_with_missing_config(self, mock_config):
        """Health endpoint should work even with missing config"""
        mock_config.SPREADSHEET_ID = None

        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')


class TestSuccessfulWorkflow(unittest.TestCase):
    """Test complete successful leave request workflow"""

    @patch('src.web.webhook.config')
    @patch('src.web.webhook.parse_leave_request')
    @patch('src.web.webhook.log_request_to_sheet')
    @patch('src.web.webhook.send_to_admin')
    def test_complete_success_workflow(self, mock_send, mock_log, mock_parse, mock_config):
        """Complete workflow: message → parse → log → confirm"""
        # Setup config
        mock_config.LINE_TEACHER_GROUP_ID = "teacher_group"
        mock_config.LINE_ADMIN_GROUP_ID = "admin_group"

        # Mock successful parsing
        mock_parse.return_value = {
            'teacher_name': 'สุกฤษฎิ์',
            'date': '2025-11-26',
            'periods': [1, 2, 3],
            'reason': 'ป่วย',
            'leave_type': 'leave'
        }

        # Process message
        test_message = "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3 ป่วย"
        webhook.process_leave_request_message(test_message, "teacher_group", "reply_token")

        # Verify workflow steps
        # 1. Parser called
        mock_parse.assert_called_once_with(test_message)

        # 2. Logged to sheets
        mock_log.assert_called_once()
        log_args = mock_log.call_args
        self.assertEqual(log_args[1]['raw_message'], test_message)
        self.assertEqual(log_args[1]['status'], "Success (AI)")

        # 3. Confirmation sent to admin
        mock_send.assert_called_once()
        confirmation = mock_send.call_args[0][0]
        self.assertIn('สุกฤษฎิ์', confirmation)
        self.assertIn('2025-11-26', confirmation)
        self.assertIn('1, 2, 3', confirmation)


if __name__ == '__main__':
    unittest.main()
