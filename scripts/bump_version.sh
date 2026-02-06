#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/bump_version.sh [patch|minor|major]
#
# Output: Prints new tag (e.g., v1.0.3) to stdout

BUMP_TYPE="${1:-patch}"

case "$BUMP_TYPE" in
  patch|minor|major)
    ;;
  *)
    echo "Usage: $0 [patch|minor|major]" >&2
    exit 1
    ;;
esac

# Get latest existing tag (fallback to v0.0.0 if none)
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

# Strip the leading 'v' and split into MAJOR.MINOR.PATCH
VERSION="${LATEST_TAG#v}"

IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

# Safety: if something goes wrong, default to 0.0.0
MAJOR=${MAJOR:-0}
MINOR=${MINOR:-0}
PATCH=${PATCH:-0}

case "$BUMP_TYPE" in
  patch)
    PATCH=$((PATCH + 1))
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
esac

NEW_TAG="v${MAJOR}.${MINOR}.${PATCH}"

echo "$NEW_TAG"