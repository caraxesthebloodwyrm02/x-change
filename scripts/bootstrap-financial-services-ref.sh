#!/usr/bin/env bash
# Shallow clone Anthropic financial-services for local skill / MCP / cookbook reference.
# Output is gitignored at third_party/anthropic-financial-services/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${ROOT}/third_party/anthropic-financial-services"
REPO="${FINANCIAL_SERVICES_REPO_URL:-https://github.com/anthropics/financial-services.git}"

if [[ -d "${TARGET}/.git" ]]; then
  echo "Already present: ${TARGET}"
  echo "To refresh: rm -rf ${TARGET} && $0"
  exit 0
fi

mkdir -p "${ROOT}/third_party"
git clone --depth 1 "${REPO}" "${TARGET}"
echo "Cloned reference to ${TARGET}"
echo "See docs/anthropic-financial-services-integration.md"
