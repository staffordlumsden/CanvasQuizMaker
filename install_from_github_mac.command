#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECTED_REPO_URL="$(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null || true)"
DEFAULT_REPO_URL="${DETECTED_REPO_URL:-https://github.com/staffordlumsden/CanvasQuizMaker.git}"
REPO_URL="${1:-$DEFAULT_REPO_URL}"
INSTALL_DIR="${2:-$HOME/CanvasQuizBuilder}"
DESKTOP_DIR="$HOME/Desktop"

echo "Installing Canvas Quiz Builder"
echo "Repo: ${REPO_URL}"
echo "Install dir: ${INSTALL_DIR}"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required but not found." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but not found." >&2
  exit 1
fi

mkdir -p "$(dirname "$INSTALL_DIR")"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  INSTALLED_REMOTE_URL="$(git -C "$INSTALL_DIR" remote get-url origin 2>/dev/null || true)"
  if [[ -n "$INSTALLED_REMOTE_URL" && "$INSTALLED_REMOTE_URL" != "$REPO_URL" ]]; then
    echo "Error: existing install at $INSTALL_DIR points to a different repo:" >&2
    echo "  $INSTALLED_REMOTE_URL" >&2
    echo "Expected:" >&2
    echo "  $REPO_URL" >&2
    echo "Remove $INSTALL_DIR or provide a different install directory." >&2
    exit 1
  fi
  echo "Existing clone found. Pulling latest changes..."
  git -C "$INSTALL_DIR" pull --ff-only
elif [[ -d "$INSTALL_DIR" ]]; then
  echo "Error: $INSTALL_DIR exists but is not a git repository." >&2
  exit 1
else
  echo "Cloning repository..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

if [[ ! -f "$INSTALL_DIR/setup_text2qti.sh" ]]; then
  echo "Error: setup_text2qti.sh not found in $INSTALL_DIR" >&2
  exit 1
fi

chmod +x "$INSTALL_DIR/setup_text2qti.sh"
chmod +x "$INSTALL_DIR/run_text2qti_web.sh"

echo "Running setup..."
"$INSTALL_DIR/setup_text2qti.sh"

LAUNCHER_PATH="$DESKTOP_DIR/Canvas Quiz Builder.command"
cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$INSTALL_DIR"
./run_text2qti_web.sh
EOF
chmod +x "$LAUNCHER_PATH"

echo
echo "Install complete."
echo "Desktop launcher created: $LAUNCHER_PATH"
echo "Double-click it to start the app."
