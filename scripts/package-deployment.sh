#!/usr/bin/env bash
# Build a zip of site files aligned with .cpanel.yml excludes (.git, .cpanel.yml, .gitignore).
# Usage: from repo root: bash scripts/package-deployment.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/ai-career-transition-deploy.zip"
cd "$ROOT"
rm -f "$OUT"
zip -r "$OUT" . \
  -x ".git/*" \
  -x ".cpanel.yml" \
  -x ".gitignore" \
  -x ".DS_Store" \
  -x "*/.DS_Store" \
  -x "ai-career-transition-deploy.zip"
echo "Wrote $OUT"
