
# Okta → Azure Communication Services (ACS) SMS Provider (Azure Functions • Python)

This Function receives Okta **Telephony Inline Hook** requests and sends OTP SMS using **Azure Communication Services (ACS)** (e.g., a short code or long code). It returns the Okta-required `commands` payload with `status` (`SUCCESS` or `FAILED`) and an ACS transaction/message ID.

## Why this exists
- Keep Okta’s SMS MFA while sending through your own ACS telephony.
- Keep the function fast and observable, with optional delivery reports.

## Architecture

Okta (Telephony Inline Hook) → Azure Function (HTTP trigger) → ACS SMS  
(Optional): ACS → Event Grid → Function/App Insights for delivery reports

```

okta-telephony-acs-sms-provider/
├── host.json
├── local.settings.json             # local dev only; never commit secrets
├── requirements.txt
├── telephony\_hook/
│   ├── **init**.py                 # HTTP-triggered function
│   └── function.json
├── sample/
│   └── request.json                # sample Okta payload for local tests
└── scripts/
└── curl-test.sh                # quick local test script

````

---

## Prerequisites

**Okta**
- An **Inline Hook** configured for *Telephony*.  
- Hook auth (Basic or OAuth 2.0).  
- Note: Telephony hooks are synchronous and expect a fast response (a few seconds). Keep your code and hosting plan sized accordingly.

**Azure**
- An **Azure Communication Services** resource with SMS enabled (short code, toll-free, or long code that your use case/region supports).
- An **Azure Function App** (Python) with Application Settings for secrets.

---

## Configuration

Set these settings (names can be changed to match your code). For local dev, use `local.settings.json`. In Azure, set as **Application Settings** on the Function App. For production, prefer **Key Vault** references.

| Setting                   | Purpose                                                   | Example / Notes                                 |
|---------------------------|-----------------------------------------------------------|--------------------------------------------------|
| `OKTA_USER`               | Fixed Basic username (if using Basic)                    | `okta`                                          |
| `OKTA_BASIC_SECRET`       | Shared secret for Basic auth                             | Store in Key Vault / App Settings               |
| `ACS_CONNECTION_STRING`   | ACS connection string                                    | From ACS “Keys”                                  |
| `ACS_SENDER`              | Sender ID (short code, toll-free, or E.164 number)       | e.g., `12345` or `+15551234567`                 |

> If you’re using OAuth 2.0 for the Okta hook instead of Basic, document those settings here and remove the Basic ones.

---

## Local Development

1) **Create virtualenv & install**
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate ; macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
````

2. **Run**

```bash
func start
```

3. **Test locally**

```bash
bash scripts/curl-test.sh
# or manually:
curl -sS -X POST "http://localhost:7071/api/<function-route>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <base64(okta:<OKTA_BASIC_SECRET>)>" \
  --data @sample/request.json | jq
```

> Replace `<function-route>` with your function route name. By default this is the **function folder name** unless overridden in `function.json`.

---

## Deploy to Azure

Using Azure Functions Core Tools:

```bash
# From repo root:
func azure functionapp publish <your-function-app-name>
```

(Optionally add GitHub Actions or Azure DevOps for CI/CD. I can provide a workflow if you’d like.)

---

## Okta Inline Hook Setup

* **Invoke URL**: `https://<your-function-app>.azurewebsites.net/api/<function-route>`
* **Auth**:

  * **Basic**: `Authorization: Basic <base64(okta:<OKTA_BASIC_SECRET>)>`
  * or **OAuth 2.0** client credentials if you prefer not to use static secrets.
* Enable the **Phone (SMS)** authenticator and preview to verify `status: "SUCCESS"` responses.

**Sample Okta request body**

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

**Sample function response shape (simplified)**

```json
{
  "commands": [
    {
      "type": "com.okta.telephony.action",
      "value": {
        "status": "SUCCESS",
        "provider": "ACS",
        "transactionId": "message-id-or-correlation",
        "transactionMetadata": "shortcode"
      }
    }
  ]
}
```

---

## Delivery Status (Recommended)

For operational visibility:

* Create an **Event Grid Subscription** on ACS for `SMSDeliveryReportReceived`.
* Handle events with another Function (EventGrid trigger) and write to **Application Insights** (or storage/queue) for auditing and alerting.
* Correlate with `transactionId` (message ID) returned by ACS.

I can add a sample Event Grid handler on request.

---

## Security Notes

* Keep responses fast to avoid Okta timeouts; fail fast and return `FAILED` instead of letting requests time out.
* Store secrets in **Key Vault**; reference them from Function App settings.
* Consider Function App **Access Restrictions** or front with **API Management**.
* Prefer **OAuth 2.0** over Basic for hook auth when feasible.

---

## Troubleshooting

| Symptom                                    | Likely Cause                       | Fix                                                                      |
| ------------------------------------------ | ---------------------------------- | ------------------------------------------------------------------------ |
| `401 Unauthorized` from function           | Bad/missing `Authorization` header | Verify Okta hook auth settings and secret/client credentials             |
| Okta reports timeout                       | Cold start / long ACS call         | Use a suitable plan, pre-warm, handle timeouts, return fast on errors    |
| ACS shows accepted but user didn’t get SMS | Carrier filtering / invalid number | Wire up delivery reports; check `transactionId` path                     |
| `400` from function                        | Payload shape differs              | Validate `phoneNumber`, `otpCode`, `deliveryChannel == "SMS"` in handler |

---
