#!/usr/bin/env bash

set -e

YELLOW='\033[93m'
GREEN='\033[92m'
RED='\033[91m'
CYAN='\033[96m'
GRAY='\033[90m'
BD='\033[1m'
R='\033[0m'

INSTALL_PATH="/usr/local/bin/helios"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELIOS_SRC="$SCRIPT_DIR/helios.py"

echo -e "${YELLOW}${BD}"
echo "  ██╗  ██╗███████╗██╗     ██╗ ██████╗ ███████╗"
echo "  ██║  ██║██╔════╝██║     ██║██╔═══██╗██╔════╝"
echo "  ███████║█████╗  ██║     ██║██║   ██║███████╗"
echo "  ██╔══██║██╔══╝  ██║     ██║██║   ██║╚════██║"
echo "  ██║  ██║███████╗███████╗██║╚██████╔╝███████║"
echo "  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚══════╝${R}"
echo -e "${YELLOW}        ☀  Installer  ☀${R}\n"

# ── Uninstall mode
if [[ "$1" == "--uninstall" ]]; then
    echo -e "${GRAY}Removing HELIOS...${R}"
    if [[ -f "$INSTALL_PATH" ]]; then
        sudo rm -f "$INSTALL_PATH"
        echo -e "${GREEN}✔ Removed $INSTALL_PATH${R}"
    else
        echo -e "${YELLOW}⚠ HELIOS is not installed at $INSTALL_PATH${R}"
    fi
    echo -e "${GRAY}Done.${R}\n"
    exit 0
fi

# ── Check OS
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}✗ HELIOS only supports Linux. Detected: $OSTYPE${R}\n"
    exit 1
fi

echo -e "${GRAY}Detected OS: $(uname -s) $(uname -r)${R}"

# ── Check helios.py exists
if [[ ! -f "$HELIOS_SRC" ]]; then
    echo -e "${RED}✗ helios.py not found in $SCRIPT_DIR${R}"
    echo -e "${GRAY}  Make sure install.sh is in the same folder as helios.py${R}\n"
    exit 1
fi

# ── Check Python 3
echo -ne "${GRAY}Checking Python 3...  ${R}"
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1)
    echo -e "${GREEN}✔ $PYVER${R}"
else
    echo -e "${RED}✗ Python 3 not found${R}"
    echo -e "${GRAY}  Install it with: sudo apt install python3${R}\n"
    exit 1
fi

# ── Check pip
echo -ne "${GRAY}Checking pip...       ${R}"
if python3 -m pip --version &>/dev/null; then
    echo -e "${GREEN}✔ pip available${R}"
else
    echo -e "${YELLOW}⚠ pip not found, attempting install...${R}"
    sudo apt-get install -y python3-pip -qq || {
        echo -e "${RED}✗ Could not install pip. Run: sudo apt install python3-pip${R}\n"
        exit 1
    }
fi

# ── Install psutil
echo -ne "${GRAY}Installing psutil...  ${R}"
if python3 -c "import psutil" &>/dev/null; then
    echo -e "${GREEN}✔ already installed${R}"
else
    python3 -m pip install psutil --quiet --break-system-packages 2>/dev/null \
        || python3 -m pip install psutil --quiet
    echo -e "${GREEN}✔ installed${R}"
fi

# ── Copy to /usr/local/bin
echo -ne "${GRAY}Installing helios...  ${R}"
sudo cp "$HELIOS_SRC" "$INSTALL_PATH"
sudo chmod +x "$INSTALL_PATH"

# Fix shebang to use system python3
sudo sed -i '1s|.*|#!/usr/bin/env python3|' "$INSTALL_PATH"

echo -e "${GREEN}✔ installed to $INSTALL_PATH${R}"

# ── Verify
echo -ne "${GRAY}Verifying install...  ${R}"
if command -v helios &>/dev/null; then
    echo -e "${GREEN}✔ helios is in PATH${R}"
else
    echo -e "${YELLOW}⚠ helios not found in PATH${R}"
    echo -e "${GRAY}  Try: export PATH=\$PATH:/usr/local/bin${R}"
fi

echo -e "\n${YELLOW}${BD}  ✔ HELIOS installed successfully!${R}\n"
echo -e "${GRAY}  Usage:${R}"
echo -e "    ${CYAN}helios${R}              ${GRAY}# full dashboard${R}"
echo -e "    ${CYAN}helios --help${R}       ${GRAY}# show all commands${R}"
echo -e "    ${CYAN}helios --ping${R}       ${GRAY}# latency monitor${R}"
echo -e "    ${CYAN}helios --scan HOST${R}  ${GRAY}# port scanner${R}"
echo -e "    ${CYAN}helios --live${R}       ${GRAY}# real-time bandwidth${R}"
echo -e "\n  ${GRAY}To uninstall: ${CYAN}bash install.sh --uninstall${R}\n"
