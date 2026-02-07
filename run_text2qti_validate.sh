#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${REPO_ROOT}/.venv/bin/python" "${REPO_ROOT}/text2qti_validate.py" "$@"
