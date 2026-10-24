#!/usr/bin/env bash
# BlindSpot Universal 1-Line Installer for macOS & Linux
# Usage: curl -sSL https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.sh | bash

set -euo pipefail

APP="blindspot"
INSTALL_DIR="$HOME/.blindspot/bin"
VENV_DIR="$HOME/.blindspot/venv"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          BlindSpot — Autonomous AI UX Testing              ║"
echo "║     Simulate human user personas to uncover UX flaws       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: Python 3 (3.10+) is required to install BlindSpot.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo -e "${RED}Error: BlindSpot requires Python 3.10 or higher. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${CYAN}→ Installing BlindSpot in isolated environment...${NC}"
mkdir -p "$INSTALL_DIR"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --quiet --upgrade pip
if ! "$VENV_DIR/bin/pip" install --quiet blindspot 2>/dev/null; then
    echo -e "${YELLOW}Notice: Installing latest package from repository...${NC}"
    "$VENV_DIR/bin/pip" install --quiet "git+https://github.com/harshit-dev-on/BlindSpot.git"
fi

# Create symlink/wrapper script in ~/.blindspot/bin
cat << 'EOF' > "$INSTALL_DIR/blindspot"
#!/usr/bin/env bash
exec "$HOME/.blindspot/venv/bin/blindspot" "$@"
EOF
chmod +x "$INSTALL_DIR/blindspot"

# Auto-provision Chromium browser binary
echo -e "${CYAN}→ Provisioning headless browser engine...${NC}"
"$VENV_DIR/bin/python" -m playwright install chromium --quiet || true

# Add to PATH in shell profile if not already present
add_path() {
    local profile="$1"
    if [ -f "$profile" ] && ! grep -q ".blindspot/bin" "$profile"; then
        echo "" >> "$profile"
        echo '# BlindSpot CLI' >> "$profile"
        echo 'export PATH="$HOME/.blindspot/bin:$PATH"' >> "$profile"
        echo -e "${GREEN}✓ Added BlindSpot to $profile${NC}"
    fi
}

add_path "$HOME/.bashrc"
add_path "$HOME/.zshrc"
add_path "$HOME/.profile"

echo -e "\n${GREEN}✓ BlindSpot successfully installed!${NC}\n"
echo -e "To get started:"
echo -e "  1. Restart your terminal or run: ${CYAN}export PATH=\"$HOME/.blindspot/bin:\$PATH\"${NC}"
echo -e "  2. Configure your AI model:      ${CYAN}blindspot setup${NC}"
echo -e "  3. Run your first audit:         ${CYAN}blindspot inspect --url https://example.com${NC}\n"
