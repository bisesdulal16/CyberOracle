#!/usr/bin/env bash
set -e

BASE="http://cyberoracle.eng.unt.edu:8009"

if [[ -z "${TOKEN_ADMIN:-}" ]]; then
  echo "TOKEN_ADMIN is not set. Run:"
  echo "eval \$(CYBERORACLE_URL=$BASE ./scripts/auth_all_roles.sh --export)"
  exit 1
fi

echo "Generating DLP block event..."
curl -s -X POST "$BASE/logs/ingest" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"endpoint":"/test","method":"POST","status_code":400,"message":"SSN 123-45-6789 BLOCKED"}'

echo ""
echo "Generating brute-force simulation..."
for i in {1..20}; do
  curl -s -X POST "$BASE/logs/ingest" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN_ADMIN" \
    -d "{\"endpoint\":\"/login\",\"method\":\"POST\",\"status_code\":401,\"message\":\"Failed login attempt-$i BLOCKED\"}" >/dev/null
done

echo "Generating SQL injection simulation..."
for i in {1..10}; do
  curl -s -X POST "$BASE/logs/ingest" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN_ADMIN" \
    -d "{\"endpoint\":\"/search\",\"method\":\"GET\",\"status_code\":400,\"message\":\"Injection ' OR 1=1 -- BLOCKED\"}" >/dev/null
done

echo "Generating normal traffic..."
for i in {1..30}; do
  curl -s -X POST "$BASE/logs/ingest" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN_ADMIN" \
    -d "{\"endpoint\":\"/profile\",\"method\":\"GET\",\"status_code\":200,\"message\":\"User profile retrieved\"}" >/dev/null
done

echo ""
echo "Recent logs:"
docker exec -it cyberoracle-db-1 psql -U postgres -d cyberoracle \
  -c "SELECT id, endpoint, status_code, severity, policy_decision, message FROM logs ORDER BY id DESC LIMIT 10;"
