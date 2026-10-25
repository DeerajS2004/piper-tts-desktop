#!/bin/bash
# Piper TTS Desktop — Install Script
# Installs English + Japanese voices and sets up a local venv.
# Usage: ./scripts/install.sh

set -euo pipefail

# ---- colours ---------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()      { echo -e "${GREEN}[ OK ]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()     { echo -e "${RED}[ERR ]${NC} $*" >&2; exit 1; }

# ---- paths -----------------------------------------------------------------
INSTALL_DIR="$HOME/.local/share/piper-tts"
VOICES_DIR="$INSTALL_DIR/voices"
VENV="$INSTALL_DIR/venv"
APP_DST="$INSTALL_DIR/app"
LAUNCHER="$HOME/.local/bin/piper-tts"
DESKTOP="$HOME/.local/share/applications/piper-tts.desktop"

# ---- voice URLs (huggingface main branch — always up to date) ---------------
EN_NAME="en_US-lessac-medium"
EN_ONNX_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
EN_JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

JA_NAME="ja_JP-hi_fi_captain-medium"
JA_ONNX_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/hi_fi_captain/medium/ja_JP-hi_fi_captain-medium.onnx"
JA_JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/hi_fi_captain/medium/ja_JP-hi_fi_captain-medium.onnx.json"

# ---- helper: download with wget or curl ------------------------------------
download() {   # download <url> <dest>
    local url="$1" dest="$2"
    if command -v wget &>/dev/null; then
        wget -q --show-progress -O "$dest" "$url"
    elif command -v curl &>/dev/null; then
        curl -L --progress-bar -o "$dest" "$url"
    else
        die "Neither wget nor curl found — install one and retry."
    fi
}

# ============================================================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}   Piper TTS Desktop — Installer           ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ---- locate project root ---------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[[ -f "$PROJECT_DIR/app/piper_gui.py" ]] || \
    die "Cannot find app/piper_gui.py — run this script from the repo root."

# ---- system packages -------------------------------------------------------
info "Checking system packages…"
MISSING_PKGS=()
command -v python3          &>/dev/null || MISSING_PKGS+=(python3)
python3 -m venv --help      &>/dev/null || MISSING_PKGS+=(python3-venv)
python3 -c "import tkinter" &>/dev/null || MISSING_PKGS+=(python3-tk)
command -v aplay            &>/dev/null || MISSING_PKGS+=(alsa-utils)
command -v espeak-ng        &>/dev/null || MISSING_PKGS+=(espeak-ng)

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    info "Installing: ${MISSING_PKGS[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y "${MISSING_PKGS[@]}"
fi
ok "System packages OK"

# ---- create directories ----------------------------------------------------
info "Creating directories…"
mkdir -p "$VOICES_DIR" "$APP_DST" "$HOME/.local/bin" \
         "$HOME/.local/share/applications"
ok "Directories created"

# ---- Python virtual environment --------------------------------------------
info "Setting up Python venv at $VENV …"
if [[ ! -d "$VENV" ]]; then
    python3 -m venv "$VENV"
fi

info "Upgrading pip / setuptools / wheel…"
"$VENV/bin/pip" install --upgrade pip setuptools wheel -q

info "Installing piper-tts (English + Japanese support)…"
"$VENV/bin/pip" install "piper-tts>=1.8.0" -q

info "Installing pyopenjtalk (Japanese phonemizer)…"
"$VENV/bin/pip" install pyopenjtalk -q

ok "Python packages installed"

# Quick smoke-test
"$VENV/bin/python3" -c "import piper; print('  piper OK')"
"$VENV/bin/python3" -c "import pyopenjtalk; print('  pyopenjtalk OK')"

# ---- copy app files --------------------------------------------------------
info "Copying application files…"
cp "$PROJECT_DIR/app/piper_gui.py" "$APP_DST/"
[[ -f "$PROJECT_DIR/app/piper-icon.png" ]] && \
    cp "$PROJECT_DIR/app/piper-icon.png" "$APP_DST/"
ok "App files copied"

# ---- launcher script -------------------------------------------------------
info "Creating launcher…"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
exec "$VENV/bin/python3" "$APP_DST/piper_gui.py" "\$@"
EOF
chmod +x "$LAUNCHER"
ok "Launcher: $LAUNCHER"

# ---- desktop entry ---------------------------------------------------------
info "Creating desktop entry…"
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Piper TTS
GenericName=Text-to-Speech
Comment=Offline TTS for English and Japanese
Exec=$LAUNCHER
Icon=$APP_DST/piper-icon.png
Terminal=false
Categories=AudioVideo;Audio;Utility;Accessibility;
Keywords=TTS;speech;offline;japanese;english;
StartupNotify=true
EOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
ok "Desktop entry created"

# ---- voice download --------------------------------------------------------
download_voice() {   # download_voice <name> <onnx_url> <json_url>
    local name="$1" onnx_url="$2" json_url="$3"
    local onnx="$VOICES_DIR/$name.onnx"
    local jsn="$VOICES_DIR/$name.onnx.json"
    if [[ -f "$onnx" && -f "$jsn" ]]; then
        ok "Voice already present: $name"
        return
    fi
    info "Downloading $name …"
    download "$onnx_url" "$onnx"
    download "$json_url" "$jsn"
    local sz; sz=$(du -h "$onnx" | cut -f1)
    ok "Voice downloaded: $name ($sz)"
}

download_voice "$EN_NAME" "$EN_ONNX_URL" "$EN_JSON_URL"
download_voice "$JA_NAME" "$JA_ONNX_URL" "$JA_JSON_URL"

# ---- quick TTS smoke-test --------------------------------------------------
info "Testing English TTS…"
if echo "hello" | "$VENV/bin/piper" \
    --model "$VOICES_DIR/$EN_NAME.onnx" \
    --output_file /tmp/piper_test_en.wav 2>&1; then
    ok "English TTS: OK"
else
    warn "English TTS self-test failed — check output above"
fi

info "Testing Japanese TTS…"
if echo "konnichiwa" | "$VENV/bin/piper" \
    --model "$VOICES_DIR/$JA_NAME.onnx" \
    --output_file /tmp/piper_test_ja.wav 2>&1; then
    ok "Japanese TTS: OK"
else
    warn "Japanese TTS self-test failed — check output above"
fi

# ---- done ------------------------------------------------------------------
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Installation complete!                  ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Launch: piper-tts"
echo "  Or via app menu: search 'Piper TTS'"
echo ""
echo "  Voices installed:"
ls -lh "$VOICES_DIR"/*.onnx 2>/dev/null | awk '{print "    " $5, $9}'
echo ""
