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

mkdir -p "$INSTALL_DIR"

# Braille animation spinner
spin() {
    local pid=$1
    local msg="$2"
    local delay=0.08
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf "\r%c %s" "$spinstr" "$msg"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
    done
    printf "\r\033[K"
}

run_spinner() {
    local msg="$1"
    shift
    "$@" >/dev/null 2>&1 &
    local pid=$!
    spin "$pid" "$msg"
    wait "$pid"
}

# 1. Setup isolated venv environment
if [ ! -d "$VENV_DIR" ]; then
    run_spinner "setting up isolated environment" python3 -m venv "$VENV_DIR"
fi

# 2. Install / upgrade BlindSpot
if [ -f "./pyproject.toml" ]; then
    run_spinner "installing blindspot" "$VENV_DIR/bin/pip" install --quiet --upgrade -e .
else
    run_spinner "installing blindspot" "$VENV_DIR/bin/pip" install --quiet --upgrade "git+https://github.com/harshit-dev-on/BlindSpot.git"
fi

# 3. Create symlink/wrapper script in ~/.blindspot/bin
cat << 'EOF' > "$INSTALL_DIR/blindspot"
#!/usr/bin/env bash
exec "$HOME/.blindspot/venv/bin/blindspot" "$@"
EOF
chmod +x "$INSTALL_DIR/blindspot"

# 4. Provision browser engine
run_spinner "provisioning headless browser engine" "$VENV_DIR/bin/python" -m playwright install chromium || true

# 5. Add to PATH in shell profile if not already present
add_path() {
    local profile="$1"
    if [ -f "$profile" ] && ! grep -q ".blindspot/bin" "$profile"; then
        echo "" >> "$profile"
        echo '# BlindSpot CLI' >> "$profile"
        echo 'export PATH="$HOME/.blindspot/bin:$PATH"' >> "$profile"
    fi
}

add_path "$HOME/.bashrc"
add_path "$HOME/.zshrc"
add_path "$HOME/.profile"

# 6. Terminal completion output
py_ver=$("$VENV_DIR/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e "  installed package blindspot 0.1.0, installed using Python $py_ver"
echo -e "  These apps are now available"
echo -e "    - blindspot"
echo -e "done! ✨ 🌟 ✨"

echo ""
echo -e "  ${CYAN}● BLINDSPOT${NC}"
echo -e "    ${MUTED}Autonomous AI UX & Usability Testing Agent${NC}"
echo ""
echo ""
echo -e "${MUTED}To get started:${NC}"
echo ""
echo -e "  ${CYAN}1.${NC} Set your environment:"
echo -e "     ${MUTED}export BLINDSPOT_LLM='gemini/gemini-2.5-flash'${NC}"
echo -e "     ${MUTED}export LLM_API_KEY='your-api-key'${NC}"
echo -e "     ${MUTED}(or run 'blindspot setup' to configure interactively)${NC}"
echo ""
echo -e "  ${CYAN}2.${NC} Run a UX & accessibility audit:"
echo -e "     ${MUTED}blindspot --target https://example.com${NC}"
echo ""
echo -e "${MUTED}For more information visit ${NC}https://github.com/harshit-dev-on/BlindSpot"
echo -e "${MUTED}Supported models: Gemini, OpenAI, Claude, OpenRouter, Ollama${NC}"
echo -e "${MUTED}Join our community ${NC}https://github.com/harshit-dev-on/BlindSpot"
echo ""
echo -e "${YELLOW}→${NC} Run ${MUTED}source ~/.$(basename "$SHELL")rc${NC} or open a new terminal"
echo ""
