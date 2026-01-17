#!/bin/bash
# Find where voices are installed
if [ -d "$HOME/.local/share/piper-tts/voices" ]; then
    VOICES_DIR="$HOME/.local/share/piper-tts/voices"
else
    VOICES_DIR="/usr/local/share/piper-tts/voices"
fi

# Run the app
cd "$(dirname "$0")/../app"
python3 piper_gui.py --voices-dir="$VOICES_DIR"
