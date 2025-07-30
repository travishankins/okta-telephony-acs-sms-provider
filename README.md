
# Okta → Azure Communication Services (ACS) SMS (Short Code) — Azure Function (Python)

This Azure Function receives **Okta Telephony Inline Hook** calls and sends the OTP via **Azure Communication Services (ACS)** using a **short code** as the sender. It returns the Okta-required `commands` payload with `SUCCESS/FAILED` and an ACS `transactionId` for correlation.

## Structure
```
okta-acs-telephony-python/
├── host.json
├── local.settings.json        # sample; do not commit secrets
├── requirements.txt
├── telephony_hook/
│   ├── __init__.py            # Function code (HTTP trigger)
│   └── function.json
├── sample/
│   └── request.json           # sample Okta payload for local testing
└── scripts/
    └── curl-test.sh           # quick curl to test locally
```

## Local development
1. Install Python 3.10+ and Azure Functions Core Tools.
2. `python -m venv .venv && source .venv/bin/activate` (PowerShell: `.venv\\Scripts\\Activate`)
3. `pip install -r requirements.txt`
4. `func start`
5. In another shell, run the curl script below.

## Sample request (Okta → Function)
```json
{
  "data": {
    "messageProfile": {
      "phoneNumber": "+15551234567",
      "otpCode": "123456",
      "deliveryChannel": "SMS",
      "msgTemplate": "Your verification code is ${otpCode}"
    }
  }
}
```

## Test with curl (local)
Update `OKTA_BASIC_SECRET` and run:
```bash
bash scripts/curl-test.sh
```

## Okta Inline Hook setup (prod)
- **Invoke URL**: `https://<your-func>.azurewebsites.net/api/okta-telephony`
- **Authentication header**: `Authorization: Basic <base64(okta:<secret>)>`
- Enable **Phone (SMS)** authenticator in the sign‑on policy.
- Use the **Preview** action in Okta Admin to verify `status: SUCCESS` response.
