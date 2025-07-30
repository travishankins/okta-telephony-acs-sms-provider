
"""
Okta Telephony Inline Hook -> Azure Communication Services (ACS) SMS (short code)

Purpose:
- Receive Okta's telephony inline hook (OTP request) over HTTPS.
- Validate caller (optional Basic auth).
- Send the OTP to the end-user via ACS SMS using a SHORT CODE as the sender.
- Return an Okta-formatted "commands" response with SUCCESS/FAILED and a transactionId.

Environment variables:
- ACS_CONNECTION_STRING : ACS connection string (endpoint + access key)
- ACS_FROM_SHORTCODE    : The short code to use as the sender (e.g., "12345")
- OKTA_BASIC_SECRET     : If set, require header Authorization: Basic base64("okta:<secret>")

Notes:
- We always respond HTTP 200 so Okta can decide how to proceed, with status in the payload.
- Keep the handler fast (<~3s). Avoid waiting for downstream delivery receipts (handle asynchronously).
"""

import os, json, base64, logging
import azure.functions as func
from azure.communication.sms import SmsClient

OKTA_USER = "okta"  # Fixed Basic-auth username that Okta will use

def _ok(resp_status: str, message_id: str = "unknown", meta: str = "shortcode"):
    """
    Build the Okta inline-hook response in the required "commands" shape.
    """
    return {
        "commands": [
            {
                "type": "com.okta.telephony.action",
                "value": {
                    "status": resp_status,           # "SUCCESS" | "FAILED"
                    "provider": "ACS",
                    "transactionId": message_id,     # Correlate with ACS messageId where possible
                    "transactionMetadata": meta      # Free-form string for troubleshooting
                }
            }
        ]
    }

def _authorized(req: func.HttpRequest) -> bool:
    """
    Optional Basic-auth gate. If OKTA_BASIC_SECRET is set, require:
      Authorization: Basic base64("okta:<secret>")
    """
    secret = os.getenv("OKTA_BASIC_SECRET")
    if not secret:
        return True  # Auth disabled if no secret configured
    auth = req.headers.get("authorization", "")
    expected = "Basic " + base64.b64encode(f"{OKTA_USER}:{secret}".encode()).decode()
    return auth == expected

def _render_message(template: str, code: str) -> str:
    """
    Fill the outbound SMS with the OTP code. Supports ${otpCode}, {{otpCode}}, {otpCode}.
    """
    if not template:
        return f"Your verification code is {code}"
    out = template
    out = out.replace("${otpCode}", code).replace("{{otpCode}}", code).replace("{otpCode}", code)
    return out

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entrypoint (HTTP trigger).
    """
    try:
        # (1) Caller authorization
        if not _authorized(req):
            return func.HttpResponse(json.dumps(_ok("FAILED", meta="unauthorized")),
                                     status_code=200, mimetype="application/json")

        # (2) Parse JSON body from Okta
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(json.dumps(_ok("FAILED", meta="invalid_json")),
                                     status_code=200, mimetype="application/json")

        mp = (body.get("data") or {}).get("messageProfile") or {}
        phone = (mp.get("phoneNumber") or "").strip()
        code = str(mp.get("otpCode") or "")
        channel = (mp.get("deliveryChannel") or "SMS").upper()
        template = mp.get("msgTemplate")

        # (3) Validate inputs (SMS only here)
        if not phone or not code or channel != "SMS":
            return func.HttpResponse(json.dumps(_ok("FAILED", meta="missing/unsupported")),
                                     status_code=200, mimetype="application/json")

        # (4) ACS config
        conn = os.getenv("ACS_CONNECTION_STRING")
        from_shortcode = os.getenv("ACS_FROM_SHORTCODE")  # e.g., "12345"
        if not conn or not from_shortcode:
            return func.HttpResponse(json.dumps(_ok("FAILED", meta="missing ACS config")),
                                     status_code=200, mimetype="application/json")

        # (5) Send via ACS
        sms = SmsClient.from_connection_string(conn)
        message = _render_message(template, code)
        result = sms.send(
            from_=from_shortcode,
            to=[phone],
            message=message,
            enable_delivery_report=True
        )

        first = result[0] if isinstance(result, list) else result
        ok = getattr(first, "successful", False)
        message_id = getattr(first, "message_id", None) or getattr(first, "messageId", None) or "unknown"

        # (6) Respond to Okta
        return func.HttpResponse(json.dumps(_ok("SUCCESS" if ok else "FAILED", message_id=message_id)),
                                 status_code=200, mimetype="application/json")

    except Exception as e:
        logging.exception("Hook error")
        return func.HttpResponse(json.dumps(_ok("FAILED", meta="exception")),
                                 status_code=200, mimetype="application/json")
