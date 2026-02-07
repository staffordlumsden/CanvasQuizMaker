#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-https://github.com/gpoore/text2qti.git}"
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
