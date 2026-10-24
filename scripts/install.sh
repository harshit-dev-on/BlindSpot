#!/usr/bin/env bash
# BlindSpot Universal 1-Line Installer for macOS & Linux
# Usage: curl -sSL https://raw.githubusercontent.com/harshit-dev-on/BlindSpot/master/scripts/install.sh | bash

set -euo pipefail

APP="blindspot"
INSTALL_DIR="$HOME/.blindspot/bin"
VENV_DIR="$HOME/.blindspot/venv"

MUTED='\033[0;2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check for Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: Python 3 (3.10+) is required to install BlindSpot.${NC}"
    exit 1
fi

echo -e "${CYAN}→ Installing BlindSpot in isolated environment...${NC}"
mkdir -p "$INSTALL_DIR"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

if [ -f "./pyproject.toml" ]; then
    "$VENV_DIR/bin/pip" install --quiet -e .
else
    "$VENV_DIR/bin/pip" install --quiet --upgrade "git+https://github.com/harshit-dev-on/BlindSpot.git"
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

echo -e "${GREEN}✓ BlindSpot ready${NC}"
echo ""
echo -e "${CYAN}"
echo "   ██████╗ ██╗     ██╗███╗   ██╗██████╗ ███████╗██████╗  ██████╗ ████████╗"
echo "   ██╔══██╗██║     ██║████╗  ██║██╔══██╗██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝"
echo "   ██████╔╝██║     ██║██╔██╗ ██║██║  ██║███████╗██████╔╝██║   ██║   ██║   "
echo "   ██╔══██╗██║     ██║██║╚██╗██║██║  ██║╚════██║██╔═══╝ ██║   ██║   ██║   "
echo "   ██████╔╝███████╗██║██║ ╚████║██████╔╝███████║██║     ╚██████╔╝   ██║   "
echo "   ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝      ╚═════╝    ╚═╝   "
echo -e "${NC}"
echo -e "${MUTED}  Autonomous AI UX & Usability Testing Agent${NC}"
echo ""
echo -e "${MUTED}To get started:${NC}"
echo ""
echo -e "  ${CYAN}1.${NC} Set your environment:"
echo -e "     ${MUTED}export LLM_API_KEY='your-api-key'${NC}"
echo -e "     ${MUTED}export BLINDSPOT_LLM='google/gemini-2.5-flash'${NC}"
echo -e "     ${MUTED}(or run 'blindspot setup' to configure interactively)${NC}"
echo ""
echo -e "  ${CYAN}2.${NC} Run a UX & accessibility audit:"
echo -e "     ${MUTED}blindspot --target https://example.com${NC}"
echo ""
echo -e "${MUTED}For more information visit ${NC}https://github.com/harshit-dev-on/BlindSpot"
echo -e "${MUTED}Supported models: Gemini, OpenAI, Claude, OpenRouter, Ollama${NC}"
echo ""
echo -e "${YELLOW}→${NC} Run ${MUTED}export PATH=\"$HOME/.blindspot/bin:\$PATH\"${NC} or open a new terminal"
echo ""
