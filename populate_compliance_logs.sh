#!/bin/bash

API_URL="http://localhost:8000/logs/ingest"

for i in {1..15}; do
  curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"endpoint\": \"/api/patient/$i\",
      \"method\": \"POST\",
      \"status_code\": 200,
      \"message\": \"Processed request successfully\",
      \"masked\": false
    }"
done

# Simulate auth failures (HIPAA access control evidence)
for i in {1..5}; do
  curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"endpoint\": \"/api/login\",
      \"method\": \"POST\",
      \"status_code\": 401,
      \"message\": \"Unauthorized access attempt\",
      \"masked\": false
    }"
done

# Simulate sensitive data masking (HIPAA transmission security)
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"endpoint\": \"/api/patient\",
    \"method\": \"POST\",
    \"status_code\": 200,
    \"message\": \"SSN=***MASKED***\",
    \"masked\": true
  }"

echo "✅ Compliance logs generated"