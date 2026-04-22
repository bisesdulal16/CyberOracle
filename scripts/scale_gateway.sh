#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/scale_gateway.sh [replicas]
#
# Example:
#   ./scripts/scale_gateway.sh 3
#
# Scales the CyberOracle API service in Docker Compose.

REPLICAS="${1:-2}"
SERVICE_NAME="api"

if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]] || [ "$REPLICAS" -lt 1 ]; then
  echo "Usage: $0 [replicas>=1]" >&2
  exit 1
fi

echo "Scaling service '$SERVICE_NAME' to $REPLICAS replicas..."

docker compose up -d --scale "${SERVICE_NAME}=${REPLICAS}"

echo
echo "Current running containers:"
docker compose ps

echo
echo "Health check:"
curl -s http://localhost:8000/health || true
