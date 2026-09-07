import base64
import json
import unittest
from unittest.mock import Mock, patch

import telephony_hook


class HookTests(unittest.TestCase):
    def request(self, authorization=""):
        request = Mock()
        request.headers = {"authorization": authorization}
        request.get_json.return_value = {
            "data": {"messageProfile": {
                "phoneNumber": "+15555550123", "otpCode": "123456",
                "deliveryChannel": "SMS",
            }}
        }
        return request

    @patch.dict("os.environ", {}, clear=True)
    @patch.object(telephony_hook, "SmsClient")
    def test_missing_secret_rejects_without_sending(self, client):
        response = telephony_hook.main(self.request())
        self.assertEqual(response.status_code, 401)
        client.from_connection_string.assert_not_called()

    @patch.dict("os.environ", {"OKTA_BASIC_SECRET": "test-secret"}, clear=True)
    def test_invalid_credentials_rejected(self):
        for header in ("", "Basic wrong", "Bearer token", "Basic \u00e9"):
            with self.subTest(header=header):
                self.assertEqual(telephony_hook.main(self.request(header)).status_code, 401)

    @patch.dict("os.environ", {
        "OKTA_BASIC_SECRET": "test-secret",
        "ACS_CONNECTION_STRING": "mock-connection",
        "ACS_FROM_SHORTCODE": "12345",
    }, clear=True)
    @patch.object(telephony_hook, "SmsClient")
    def test_sdk_dictionary_result(self, client):
        authorization = "Basic " + base64.b64encode(b"okta:test-secret").decode()
        for successful, expected in ((True, "SUCCESS"), (False, "FAILED")):
            with self.subTest(successful=successful):
                client.from_connection_string.return_value.send.return_value = [
                    {"successful": successful, "messageId": "message-123"}
                ]
                response = telephony_hook.main(self.request(authorization))
                value = json.loads(response.get_body())["commands"][0]["value"]
                self.assertEqual(value["status"], expected)
                self.assertEqual(value["transactionId"], "message-123")


if __name__ == "__main__":
    unittest.main()
