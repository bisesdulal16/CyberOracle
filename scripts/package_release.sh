#!/usr/bin/env bash
# scripts/package_release.sh
#
# PSFR10 — Package CyberOracle release artifacts.
#
# Creates a versioned .tar.gz containing:
#   - Dockerfile
#   - docker-compose.yml
#   - scripts/
#   - infra/k8s/
#   - terraform/
#   - docs/
#   - requirements.txt
#   - .env.example (if present)
#
# Usage:
#   bash scripts/package_release.sh [version]
#   bash scripts/package_release.sh v1.0.0

set -euo pipefail

VERSION="${1:-$(git describe --tags --always 2>/dev/null || echo 'v1.0.0')}"
RELEASE_NAME="cyberoracle-${VERSION}"
OUT_DIR="dist"
ARCHIVE="${OUT_DIR}/${RELEASE_NAME}.tar.gz"

echo "========================================"
echo "  CyberOracle Release Packager"
echo "  Version : ${VERSION}"
echo "  Output  : ${ARCHIVE}"
echo "========================================"

mkdir -p "${OUT_DIR}"

# Files and directories to include
INCLUDE=(
  Dockerfile
  docker-compose.yml
  requirements.txt
  start.sh
  scripts/
  infra/k8s/
  terraform/
  docs/DEPLOYMENT.md
  docs/TLS_SETUP.md
  docs/threat-modeling/policy.yaml
  docs/threat-modeling/STRIDE.md
  grafana/dashboards/
  grafana/provisioning/
)

# Build include args for tar
TAR_ARGS=()
for item in "${INCLUDE[@]}"; do
  [[ -e "$item" ]] && TAR_ARGS+=("$item")
done

# Also include .env.example if it exists
[[ -f ".env.example" ]] && TAR_ARGS+=(".env.example")

tar -czf "${ARCHIVE}" "${TAR_ARGS[@]}"

SIZE=$(du -sh "${ARCHIVE}" | cut -f1)

echo ""
echo "  Packaged files:"
tar -tzf "${ARCHIVE}" | sed 's/^/    /'
echo ""
echo "  Archive size : ${SIZE}"
echo "  Location     : ${ARCHIVE}"
echo ""
echo "========================================"
echo "  To create a GitHub release, run:"
echo "  gh release create ${VERSION} ${ARCHIVE} \\"
echo "    --title 'CyberOracle ${VERSION}' \\"
echo "    --notes 'Release ${VERSION} — packaged Docker artifacts, K8s manifests, Terraform configs, and deployment docs.'"
echo "========================================"
