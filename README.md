
# Okta Telephony Provider for Azure Communication Services

> **Integrate Okta SMS MFA with Azure Communication Services for enterprise-grade OTP delivery**

This Azure Function implements an Okta Telephony Inline Hook endpoint that processes OTP requests and delivers SMS messages through Azure Communication Services (ACS). It enables organizations to maintain Okta's SMS MFA capabilities while using their own Azure telephony infrastructure.

## 🎯 Key Features

- **Okta Integration** - Seamless telephony inline hook implementation
- **ACS SMS Delivery** - Support for short codes, toll-free, and long codes
- **Fast Response** - Optimized for Okta's synchronous hook requirements (<3s)
- **Secure Authentication** - Basic auth or OAuth 2.0 support
- **Delivery Tracking** - Optional Event Grid integration for delivery reports
- **Production Ready** - Comprehensive error handling and logging

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Okta (Telephony Inline Hook)                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP POST (OTP Request)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Azure Function (HTTP Trigger)                                   │
│  • Validate authentication                                      │
│  • Parse Okta payload                                           │
│  • Send SMS via ACS                                             │
│  • Return status to Okta                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Azure Communication Services                                    │
│  • SMS delivery via short code/long code                        │
│  • Delivery report generation                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ├──────────────────┬─────────────────────────┐
                     ▼                  ▼                         ▼
              ┌──────────┐      ┌──────────────┐        ┌────────────┐
              │ End User │      │ Event Grid   │        │ App        │
              │   SMS    │      │  (Optional)  │        │ Insights   │
              └──────────┘      └──────────────┘        └────────────┘
```

## 📁 Project Structure

```
okta-telephony-acs-sms-provider/
├── host.json
├── local.settings.json.example     # Copy to local.settings.json (gitignored)
├── requirements.txt
├── telephony_hook/
│   ├── __init__.py                 # Main function handler
│   └── function.json
├── sample/
│   └── request.json                # Sample Okta payload for testing
└── scripts/
    └── curl-test.sh                # Local testing script
```

---

## 📝 Prerequisites

**Okta Requirements:**
- Okta tenant with Telephony Inline Hook capability
- Authentication configured (Basic Auth or OAuth 2.0)
- Understanding that telephony hooks are synchronous (3 second timeout)

**Azure Requirements:**
- Azure Communication Services resource with SMS enabled
- Supported sender type: short code, toll-free, or long code
- Azure Function App (Python runtime)
- Azure Key Vault (recommended for secrets management)

**Development Tools:**
- Python 3.8+
- Azure Functions Core Tools
- Azure CLI

---

## ⚙️ Configuration

### Environment Variables

For local development, copy the template and fill in your values:

```bash
cp local.settings.json.example local.settings.json
```

`local.settings.json` is gitignored. In production, set these as Application Settings on the Azure Function App instead.

| Setting                   | Purpose                                                   | Example                                          |
|---------------------------|-----------------------------------------------------------|--------------------------------------------------|
| `OKTA_USER`               | Basic auth username (fixed value)                        | `okta`                                           |
| `OKTA_BASIC_SECRET`       | Shared secret for Basic authentication                   | Store in Key Vault                               |
| `ACS_CONNECTION_STRING`   | Azure Communication Services connection string           | From ACS resource "Keys" blade                   |
| `ACS_FROM_SHORTCODE`      | Sender phone number or short code                        | `12345` or `+15551234567`                        |

**Security Note:** Always use Azure Key Vault references for secrets in production environments.

---

## 🚀 Quick Start

### Local Development

**1. Set up Python environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate
pip install -r requirements.txt
```

**2. Start the function**
```bash
func start
```

The function will be available at `http://localhost:7071/api/okta-telephony`

**3. Test locally**
```bash
# Using the provided test script
bash scripts/curl-test.sh

# Or manually
curl -sS -X POST "http://localhost:7071/api/okta-telephony" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'okta:supersecret' | base64)" \
  --data @sample/request.json | jq
```

### Azure Deployment

Deploy the function to Azure:

```bash
func azure functionapp publish <your-function-app-name>
```

After deployment, configure the Application Settings in Azure Portal with your production values.

---

## 🔗 Okta Inline Hook Configuration

### Hook Setup

Configure the inline hook in your Okta admin console:

- **Endpoint URL**: `https://<your-function-app>.azurewebsites.net/api/okta-telephony`
- **Authentication**: Basic Authentication
  - Username: `okta`
  - Password: Your `OKTA_BASIC_SECRET` value

### Request Format

Okta sends the following payload:

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

### Response Format

The function returns:

```json
{
  "commands": [
    {
      "type": "com.okta.telephony.action",
      "value": {
        "status": "SUCCESS",
        "provider": "ACS",
        "transactionId": "message-id-from-acs",
        "transactionMetadata": "shortcode"
      }
    }
  ]
}
```

**Status Values:**
- `SUCCESS` - SMS sent successfully via ACS
- `FAILED` - Error occurred (authentication failure, missing config, ACS error, etc.)

Use Okta's inline hook preview feature to test the integration before enabling it for production users.

---

## 📊 Monitoring & Delivery Reports

### Application Insights

The function logs all operations to Application Insights:
- Authentication attempts
- Payload validation results
- ACS API calls and responses
- Error conditions

### Optional: SMS Delivery Reports

For full visibility into SMS delivery status:

1. **Create Event Grid Subscription** on your ACS resource:
   - Event Type: `SMSDeliveryReportReceived`
   - Endpoint: New Azure Function with Event Grid trigger

2. **Process delivery events** in the handler function:
   - Extract delivery status (Delivered, Failed, etc.)
   - Log to Application Insights
   - Correlate with `transactionId` from original request

3. **Set up alerts** for delivery failures or low success rates

This provides end-to-end observability from Okta request through to carrier delivery.

---

## 🔐 Security Considerations

**Authentication:**
- Function implements Basic authentication validation
- Okta must provide correct credentials on every request
- Consider OAuth 2.0 for enhanced security

**Secrets Management:**
- Store all secrets in Azure Key Vault
- Reference Key Vault secrets in Function App Application Settings
- Never commit `local.settings.json` to source control

**Network Security:**
- Use Function App Access Restrictions to limit inbound traffic
- Consider Azure API Management for additional security layers
- Enable HTTPS only (enforced by default)

**Performance:**
- Okta expects response within 3 seconds
- Function fails fast on errors to avoid timeouts
- Use appropriate App Service Plan for production workloads

---

## 🐛 Troubleshooting

| Issue                                      | Cause                              | Resolution                                                               |
| ------------------------------------------ | ---------------------------------- | ------------------------------------------------------------------------ |
| `401 Unauthorized` response                | Invalid Authorization header       | Verify Okta hook credentials match `OKTA_BASIC_SECRET`                   |
| Okta timeout error                         | Slow function execution            | Check App Service Plan, review Application Insights for bottlenecks      |
| `FAILED` status with valid config          | ACS API error                      | Review function logs for ACS error details, verify connection string     |
| Messages not received by users             | Carrier filtering or invalid number| Enable ACS delivery reports, verify phone number format                  |
| `400 Bad Request`                          | Malformed payload                  | Validate Okta payload contains required fields                           |

**Debugging Steps:**
1. Review Application Insights logs for detailed error messages
2. Test locally using `curl-test.sh` script
3. Verify all environment variables are configured correctly
4. Check ACS resource for SMS capability and quota
5. Confirm sender number is provisioned and enabled for SMS

---

## 📚 Additional Resources

- [Okta Telephony Inline Hook Documentation](https://developer.okta.com/docs/concepts/inline-hooks/#telephony-inline-hook)
- [Azure Communication Services SMS Documentation](https://docs.microsoft.com/azure/communication-services/concepts/sms/sdk-features)
- [Azure Functions Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)

---

<div align="center">

**Built with ❤️ following Azure Well-Architected Framework best practices**

</div>

## Contributing

Contributions welcome! Please open an issue or pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
