#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating virtual environment at ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi

echo "Upgrading pip"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip

echo "Installing text2qti"
"${VENV_DIR}/bin/python" -m pip install .

chmod +x "${REPO_ROOT}/run_text2qti_cli.sh" "${REPO_ROOT}/run_text2qti_web.sh" "${REPO_ROOT}/run_text2qti_validate.sh" "${REPO_ROOT}/install_from_github_mac.command"

cat <<'EOF'
Setup complete.
- CLI: ./run_text2qti_cli.sh
- Web: ./run_text2qti_web.sh (then open http://127.0.0.1:8001)
- Validate: ./run_text2qti_validate.sh /path/to/quiz.txt
EOF
