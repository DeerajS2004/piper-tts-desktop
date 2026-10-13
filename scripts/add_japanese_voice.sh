#!/bin/bash
# Piper TTS Desktop — Add Japanese Voice
# Downloads ja_JP-hi_fi_captain-medium voice model from Hugging Face
# Usage: chmod +x scripts/add_japanese_voice.sh && ./scripts/add_japanese_voice.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  🇯🇵 Piper TTS — Add Japanese Voice  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

VOICES_DIR="$HOME/.local/share/piper-tts/voices"
VOICE_NAME="ja_JP-hi_fi_captain-medium"
ONNX_FILE="$VOICES_DIR/$VOICE_NAME.onnx"
JSON_FILE="$VOICES_DIR/$VOICE_NAME.onnx.json"

# Correct HuggingFace URLs (main branch, hi_fi_captain voice)
ONNX_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/hi_fi_captain/medium/ja_JP-hi_fi_captain-medium.onnx"
JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/hi_fi_captain/medium/ja_JP-hi_fi_captain-medium.onnx.json"

# Check if voices dir exists
if [ ! -d "$VOICES_DIR" ]; then
    print_info "Creating voices directory at $VOICES_DIR"
    mkdir -p "$VOICES_DIR"
fi

# Check if already installed
if [ -f "$ONNX_FILE" ] && [ -f "$JSON_FILE" ]; then
    ONNX_SIZE=$(du -h "$ONNX_FILE" | cut -f1)
    print_success "Japanese voice already installed! ($ONNX_SIZE)"
    echo ""
    echo -e "${YELLOW}Voice file:${NC} $ONNX_FILE"
    echo ""
    echo "Restart Piper TTS to use the Japanese voice."
    exit 0
fi

# Check downloader
if command -v wget &>/dev/null; then
    DOWNLOADER="wget"
elif command -v curl &>/dev/null; then
    DOWNLOADER="curl"
else
    print_error "Neither wget nor curl found. Please install one and retry."
    exit 1
fi

print_info "Downloading Japanese voice model: $VOICE_NAME"
print_info "This may take a few minutes (~63 MB)..."
echo ""

# Download ONNX model
print_info "Downloading $VOICE_NAME.onnx ..."
if [ "$DOWNLOADER" = "wget" ]; then
    wget --show-progress -O "$ONNX_FILE" "$ONNX_URL" || { print_error "Download failed"; rm -f "$ONNX_FILE"; exit 1; }
else
    curl -L --progress-bar -o "$ONNX_FILE" "$ONNX_URL" || { print_error "Download failed"; rm -f "$ONNX_FILE"; exit 1; }
fi

# Download JSON config
print_info "Downloading $VOICE_NAME.onnx.json ..."
if [ "$DOWNLOADER" = "wget" ]; then
    wget --show-progress -O "$JSON_FILE" "$JSON_URL" || { print_error "Download failed"; rm -f "$JSON_FILE"; exit 1; }
else
    curl -L --progress-bar -o "$JSON_FILE" "$JSON_URL" || { print_error "Download failed"; rm -f "$JSON_FILE"; exit 1; }
fi

# Verify
if [ -f "$ONNX_FILE" ] && [ -f "$JSON_FILE" ]; then
    ONNX_SIZE=$(du -h "$ONNX_FILE" | cut -f1)
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ Japanese Voice Installed!          ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    print_success "Voice: $VOICE_NAME ($ONNX_SIZE)"
    echo -e "${YELLOW}Location:${NC} $VOICES_DIR/"
    echo ""
    echo -e "${BLUE}📌 Next steps:${NC}"
    echo "  1. Restart the Piper TTS app"
    echo "  2. Select '🇯🇵 Hi Fi Captain (Japanese)' from the voice dropdown"
    echo "  3. Type Japanese text and click ▶ Speak"
    echo ""
    echo -e "${YELLOW}💡 Tip:${NC} Install a CJK font for best rendering:"
    echo "  sudo apt install fonts-noto-cjk"
    echo ""
else
    print_error "Something went wrong. Voice files may be incomplete."
    exit 1
fi
