# Okta Telephony ACS SMS Provider

Receive Okta telephony inline hooks and submit SMS messages through ACS.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat)](LICENSE)

[Quick Start](#quick-start) | [Configuration](#configuration) | [Validation](#validation) | [Guide](GUIDE.md)

## Overview

A Python Azure Function validates Basic credentials, submits an OTP message, and returns an Okta hook outcome.
This is a sample integration. OAuth and a delivery-report consumer are not implemented.

## Prerequisites

- Python 3.12 for local tests and Azure Functions Core Tools for local hosting.
- An Okta tenant with telephony inline hooks and an ACS resource with an eligible SMS sender.
- A supported Function App runtime and secure application configuration for deployment.

## Quick Start

```text
git clone https://github.com/travishankins/okta-telephony-acs-sms-provider.git
cd okta-telephony-acs-sms-provider
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Use an isolated Python environment, then follow the [project guide](GUIDE.md) for local host and Okta hook setup.

## Configuration

Use [local.settings.json.example](local.settings.json.example) as the local template.
Configure `OKTA_BASIC_SECRET`, `ACS_CONNECTION_STRING`, and `ACS_FROM_SHORTCODE`; the Basic username is fixed to `okta`.

## Validation

Unit tests mock SMS submission and cover rejected credentials and SDK results.
Measure cold/warm hook timing and verify real carrier delivery before production rollout.

## Operations

Configure secrets before publishing: missing or invalid Basic credentials receive HTTP 401.
Use a staging slot where supported and retain the previous artifact. Verify the hook before switching traffic.

## Security and Limitations

Never log OTPs, phone numbers, authorization headers, or connection strings.
An ACS-accepted submission is not proof of delivery; synchronous hook timing remains a live integration requirement.

## Documentation

- [Project guide](GUIDE.md): configuration, request/response contracts, monitoring, and troubleshooting.
- [Sample request](sample/request.json): synthetic hook payload.

## Contributing

Open an issue or pull request with synthetic payloads and test results. Do not include real OTPs, recipient details, or credentials.

## License

[MIT License](LICENSE).
