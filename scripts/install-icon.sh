#!/bin/bash
# Install custom icon for Piper TTS

ICON_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/assets/piper-icon.png"
ICON_DEST="$HOME/.local/share/icons/piper-tts.png"
DESKTOP_FILE="$HOME/.local/share/applications/piper-tts.desktop"

echo "Installing custom icon for Piper TTS..."

# Create icons directory
mkdir -p "$HOME/.local/share/icons"

# Copy icon
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DEST"
    echo "✓ Icon copied to $ICON_DEST"
else
    echo "⚠️ Icon not found at $ICON_SRC"
    echo "Please place a 256x256 PNG icon at: assets/piper-icon.png"
    exit 1
fi

# Update desktop file to use custom icon
if [ -f "$DESKTOP_FILE" ]; then
    # Check if icon entry exists
    if grep -q "Icon=" "$DESKTOP_FILE"; then
        # Replace existing icon
        sed -i "s|Icon=.*|Icon=$ICON_DEST|" "$DESKTOP_FILE"
    else
        # Add icon entry
        echo "Icon=$ICON_DEST" >> "$DESKTOP_FILE"
    fi
    echo "✓ Desktop file updated"
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications"
        echo "✓ Desktop database updated"
    fi
else
    echo "⚠️ Desktop file not found: $DESKTOP_FILE"
    echo "Run the main installer first: ./scripts/install.sh"
fi

echo ""
echo "✅ Custom icon installed!"
echo "The icon will appear after restarting your session or logging out/in."
