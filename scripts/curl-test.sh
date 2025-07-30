#!/usr/bin/env bash
set -euo pipefail

# Change these for local testing
FUNC_URL="http://localhost:7071/api/okta-telephony"
SECRET="supersecret" # must match OKTA_BASIC_SECRET in local.settings.json

AUTH=$(printf "okta:%s" "$SECRET" | base64)

curl -sS -X POST "$FUNC_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  --data @sample/request.json | jq .
