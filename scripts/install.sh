#!/usr/bin/env bash
# =============================================================================
# Piper TTS Desktop — Java edition installer
# Installs: OpenJDK 17, Maven, native piper binary, voice models, Spring Boot JAR
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      Piper TTS Desktop Installer     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="$HOME/.local/share/piper-tts"
VOICES_DIR="$INSTALL_DIR/voices"
BIN_DIR="$INSTALL_DIR/bin"
APP_DST="$INSTALL_DIR/app"
LAUNCHER="$HOME/.local/bin/piper-tts"
DESKTOP="$HOME/.local/share/applications/piper-tts.desktop"

# Native piper binary release
PIPER_RELEASE="2023.11.14-2"
PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_RELEASE}/piper_linux_x86_64.tar.gz"
PIPER_BIN="$BIN_DIR/piper/piper"

# ── System packages ───────────────────────────────────────────────────────────
info "Checking system packages…"
MISSING=()
command -v java       &>/dev/null || MISSING+=(openjdk-17-jre-headless)
command -v mvn        &>/dev/null || MISSING+=(maven)
command -v wget       &>/dev/null || MISSING+=(wget)
command -v espeak-ng  &>/dev/null || MISSING+=(espeak-ng)

if [[ ${#MISSING[@]} -gt 0 ]]; then
    info "Installing: ${MISSING[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y "${MISSING[@]}"
fi
ok "System packages OK"

# Check Java version (need 17+)
JAVA_VER=$(java -version 2>&1 | grep -oP '\d+' | head -1)
if [[ "$JAVA_VER" -lt 17 ]]; then
    die "Java 17+ required, found Java ${JAVA_VER}. Install openjdk-17-jre-headless."
fi
ok "Java ${JAVA_VER} OK"

# ── Directories ───────────────────────────────────────────────────────────────
info "Creating directories…"
mkdir -p "$VOICES_DIR" "$BIN_DIR" "$APP_DST" "$HOME/.local/bin" \
         "$HOME/.local/share/applications"
ok "Directories ready"

# ── Native piper binary ───────────────────────────────────────────────────────
if [[ -x "$PIPER_BIN" ]]; then
    ok "Native piper binary already installed: $PIPER_BIN"
else
    info "Downloading native piper binary (${PIPER_RELEASE})…"
    TMP_TAR="$(mktemp /tmp/piper_XXXXXX.tar.gz)"
    wget -q --show-progress -O "$TMP_TAR" "$PIPER_URL" || \
        die "Failed to download piper binary from GitHub releases"
    tar -xzf "$TMP_TAR" -C "$BIN_DIR/"
    rm -f "$TMP_TAR"
    chmod +x "$PIPER_BIN"
    ok "Native piper installed: $PIPER_BIN"
fi

# Smoke-test the binary
"$PIPER_BIN" --version 2>&1 | head -1 || warn "piper --version failed (may still work)"

# ── Build Spring Boot JAR ─────────────────────────────────────────────────────
info "Building Spring Boot JAR (this takes ~30s on first run)…"
cd "$PROJECT_DIR"
mvn package -q -DskipTests 2>&1 | tail -5
JAR_SRC="$PROJECT_DIR/target/piper-tts.jar"
[[ -f "$JAR_SRC" ]] || die "Build failed — $JAR_SRC not found"
cp "$JAR_SRC" "$APP_DST/piper-tts.jar"
ok "JAR built and copied to $APP_DST/piper-tts.jar"

# ── Voice models ──────────────────────────────────────────────────────────────
info "Checking voice models…"

download_voice() {
    local name="$1" locale="$2" quality="$3"
    local base_url="https://huggingface.co/rhasspy/piper-voices/resolve/main"
    local lang_path="$4"
    local onnx_url="${base_url}/${lang_path}/${name}/${quality}/${name}-${quality}.onnx"
    local json_url="${base_url}/${lang_path}/${name}/${quality}/${name}-${quality}.onnx.json"
    local onnx_file="${VOICES_DIR}/${locale}-${name}-${quality}.onnx"
    local json_file="${VOICES_DIR}/${locale}-${name}-${quality}.onnx.json"

    if [[ -f "$onnx_file" && -f "$json_file" ]]; then
        ok "Voice already downloaded: ${locale}-${name}-${quality}"
        return
    fi
    info "Downloading ${locale}-${name}-${quality} voice…"
    wget -q --show-progress -O "$onnx_file" "$onnx_url" || { warn "ONNX download failed"; return; }
    wget -q --show-progress -O "$json_file" "$json_url" || { warn "JSON download failed"; return; }
    ok "Voice ready: ${locale}-${name}-${quality}"
}

# English
download_voice "lessac"      "en_US" "medium" "en/en_US"

# Japanese — kenjirous uses espeak-ng (works with native piper binary)
download_voice "kenjirous"   "ja_JP" "medium" "ja/ja_JP"

# ── Launcher script ───────────────────────────────────────────────────────────
info "Creating launcher…"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
# Piper TTS — Java web launcher
export PIPER_BIN="${PIPER_BIN}"
export PIPER_VOICES_DIR="${VOICES_DIR}"
exec java -jar "${APP_DST}/piper-tts.jar" "\$@"
EOF
chmod +x "$LAUNCHER"
ok "Launcher: $LAUNCHER"

# ── Desktop entry ─────────────────────────────────────────────────────────────
info "Creating desktop entry…"
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Piper TTS
GenericName=Text-to-Speech
Comment=Offline EN/JA Text-to-Speech (Java backend)
Exec=${LAUNCHER}
Terminal=false
Categories=AudioVideo;Audio;Utility;Accessibility;
Keywords=TTS;speech;offline;japanese;english;
StartupNotify=true
EOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
ok "Desktop entry created"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "  Launch:  piper-tts"
echo "  Or run:  java -jar $APP_DST/piper-tts.jar"
echo ""
echo "  The app will open your browser at http://localhost:5000"
echo ""
