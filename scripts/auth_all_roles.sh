#!/usr/bin/env bash
# Authenticates all three CyberOracle roles and prints their JWT tokens.
# Optionally exports them as environment variables.
#
# Usage:
#   ./scripts/auth_all_roles.sh                    # uses localhost:8001
#   ./scripts/auth_all_roles.sh https://example.com
#   eval $(./scripts/auth_all_roles.sh --export)   # exports TOKEN_ADMIN, TOKEN_DEV, TOKEN_AUDITOR

set -euo pipefail

# ---------------------------------------------------------------------------
# Config — override via env vars or pass a base URL as $1
# ---------------------------------------------------------------------------
BASE_URL="${1:-${CYBERORACLE_URL:-http://localhost:8001}}"
EXPORT_MODE=false

if [[ "${1:-}" == "--export" ]]; then
  EXPORT_MODE=true
  BASE_URL="${CYBERORACLE_URL:-http://localhost:8001}"
fi

ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-changeme_admin}"

DEV_USER="${DEV_USERNAME:-developer}"
DEV_PASS="${DEV_PASSWORD:-changeme_dev}"

AUDITOR_USER="${AUDITOR_USERNAME:-auditor}"
AUDITOR_PASS="${AUDITOR_PASSWORD:-changeme_auditor}"

LOGIN_URL="${BASE_URL}/auth/login"
ME_URL="${BASE_URL}/auth/me"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
check_deps() {
  for dep in curl jq; do
    if ! command -v "$dep" &>/dev/null; then
      echo "ERROR: '$dep' is required but not installed." >&2
      exit 1
    fi
  done
}

login() {
  local username="$1"
  local password="$2"

  local response
  response=$(curl -s -w "\n%{http_code}" -X POST "$LOGIN_URL" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${username}\", \"password\": \"${password}\"}")

  local body http_code
  body=$(echo "$response" | head -n -1)
  http_code=$(echo "$response" | tail -n 1)

  if [[ "$http_code" != "200" ]]; then
    echo "  [FAIL] HTTP $http_code — $(echo "$body" | jq -r '.detail // .message // .')" >&2
    echo ""
    return 1
  fi

  echo "$body"
}

verify_token() {
  local token="$1"
  local response
  response=$(curl -s -w "\n%{http_code}" "$ME_URL" \
    -H "Authorization: Bearer $token")

  local body http_code
  body=$(echo "$response" | head -n -1)
  http_code=$(echo "$response" | tail -n 1)

  if [[ "$http_code" == "200" ]]; then
    echo "$(echo "$body" | jq -r '"  verified → username=" + .username + "  role=" + .role')"
  else
    echo "  [WARN] /auth/me returned HTTP $http_code" >&2
  fi
}

print_section() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Role: $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
check_deps

if [[ "$EXPORT_MODE" == false ]]; then
  echo ""
  echo "CyberOracle — JWT Auth for All Roles"
  echo "Target: $BASE_URL"
fi

declare -A TOKENS

for role_info in "admin:${ADMIN_USER}:${ADMIN_PASS}" "developer:${DEV_USER}:${DEV_PASS}" "auditor:${AUDITOR_USER}:${AUDITOR_PASS}"; do
  ROLE="${role_info%%:*}"
  REST="${role_info#*:}"
  USER="${REST%%:*}"
  PASS="${REST#*:}"

  if [[ "$EXPORT_MODE" == false ]]; then
    print_section "$ROLE"
    echo "  Username : $USER"
  fi

  body=$(login "$USER" "$PASS") || { TOKENS[$ROLE]=""; continue; }

  token=$(echo "$body" | jq -r '.access_token')
  issued_role=$(echo "$body" | jq -r '.role')

  TOKENS[$ROLE]="$token"

  if [[ "$EXPORT_MODE" == false ]]; then
    echo "  Role     : $issued_role"
    echo "  Token    : ${token:0:40}...${token: -10}"
    verify_token "$token"
    echo ""
    echo "  Full token (copy for use in Authorization header):"
    echo "  Bearer $token"
  fi
done

if [[ "$EXPORT_MODE" == true ]]; then
  [[ -n "${TOKENS[admin]:-}" ]]     && echo "export TOKEN_ADMIN='${TOKENS[admin]}'"
  [[ -n "${TOKENS[developer]:-}" ]] && echo "export TOKEN_DEV='${TOKENS[developer]}'"
  [[ -n "${TOKENS[auditor]:-}" ]]   && echo "export TOKEN_AUDITOR='${TOKENS[auditor]}'"
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "To export tokens as env vars, run:"
  echo "  eval \$(./scripts/auth_all_roles.sh --export)"
  echo ""
  echo "Then use them in curl:"
  echo "  curl -H \"Authorization: Bearer \$TOKEN_ADMIN\" ${BASE_URL}/auth/me"
  echo "  curl -H \"Authorization: Bearer \$TOKEN_DEV\"   ${BASE_URL}/ai/query"
  echo "  curl -H \"Authorization: Bearer \$TOKEN_AUDITOR\" ${BASE_URL}/logs"
  echo ""
fi
