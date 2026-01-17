#!/bin/bash
# Piper TTS Desktop - Installation Script
# Version: 1.0.0
# Author: [Your Name]

set -e  # Exit on error
set -u  # Treat unset variables as error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Piper TTS"
APP_VERSION="1.0.0"
INSTALL_DIR="$HOME/.local/share/piper-tts"
DESKTOP_FILE="$HOME/.local/share/applications/piper-tts.desktop"
ICON_NAME="audio-card"

# Voice configurations
VOICE_NAME="en_US-lessac-medium"
VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-lessac-medium.onnx"
VOICE_JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-lessac-medium.onnx.json"

# Functions for colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}   $APP_NAME Installer v$APP_VERSION${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_warning "It's not recommended to run this script as root."
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check system requirements
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_error "pip3 not found. Installing..."
        sudo apt update && sudo apt install -y python3-pip
    fi
    
    # Check ALSA
    if command -v aplay &> /dev/null; then
        print_success "ALSA (aplay) found"
    else
        print_error "ALSA not found. Installing alsa-utils..."
        sudo apt update && sudo apt install -y alsa-utils
    fi
    
    # Check wget/curl for downloading
    if command -v wget &> /dev/null; then
        DOWNLOADER="wget -q --show-progress"
    elif command -v curl &> /dev/null; then
        DOWNLOADER="curl -L --progress-bar -O"
    else
        print_error "Neither wget nor curl found. Installing wget..."
        sudo apt update && sudo apt install -y wget
        DOWNLOADER="wget -q --show-progress"
    fi
    
    # Check for tkinter (GUI dependency)
    if python3 -c "import tkinter" &> /dev/null; then
        print_success "tkinter found"
    else
        print_error "tkinter not found. Installing..."
        sudo apt update && sudo apt install -y python3-tk
    fi
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    
    # Main installation directory
    mkdir -p "$INSTALL_DIR/app"
    mkdir -p "$INSTALL_DIR/voices"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$HOME/.local/share/applications"
    mkdir -p "$HOME/.local/bin"
    
    print_success "Directories created"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Check if virtual environment exists
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv "$INSTALL_DIR/venv"
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment and install piper-tts
    print_info "Installing piper-tts..."
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install piper-tts
    pip install piper-tts
    
    # Also install any other required packages
    pip install packaging
    
    deactivate
    
    print_success "Python dependencies installed"
}

# Copy application files
copy_application() {
    print_info "Copying application files..."
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    
    # Check if we're running from the right location
    if [ ! -f "$PROJECT_DIR/app/piper_gui.py" ]; then
        print_error "Cannot find application files!"
        print_error "Please run this script from the project directory."
        exit 1
    fi
    
    # Copy Python files
    cp "$PROJECT_DIR/app/piper_gui.py" "$INSTALL_DIR/app/"
    cp "$PROJECT_DIR/app/piper_gui_simple.py" "$INSTALL_DIR/app/"
    cp "$PROJECT_DIR/app/test_app.py" "$INSTALL_DIR/app/"
    
    # Make launcher script
    cat > "$INSTALL_DIR/app/launcher.sh" << 'EOF'
#!/bin/bash
# Piper TTS Desktop Launcher

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
if [ -f "$INSTALL_DIR/venv/bin/activate" ]; then
    source "$INSTALL_DIR/venv/bin/activate"
else
    echo "ERROR: Virtual environment not found at $INSTALL_DIR/venv"
    exit 1
fi

# Set voice directory
VOICES_DIR="$INSTALL_DIR/voices"
if [ ! -d "$VOICES_DIR" ]; then
    echo "ERROR: Voices directory not found at $VOICES_DIR"
    exit 1
fi

# Run the application
cd "$SCRIPT_DIR"
python3 piper_gui.py --voices-dir="$VOICES_DIR" "$@"

# Deactivate virtual environment
deactivate
EOF
    
    chmod +x "$INSTALL_DIR/app/launcher.sh"
    
    # Create a symlink in ~/.local/bin for command line access
    ln -sf "$INSTALL_DIR/app/launcher.sh" "$HOME/.local/bin/piper-tts"
    
    print_success "Application files copied"
}

# Download voice files
download_voices() {
    print_info "Checking voice files..."
    
    VOICE_ONNX="$INSTALL_DIR/voices/$VOICE_NAME.onnx"
    VOICE_JSON="$INSTALL_DIR/voices/$VOICE_NAME.onnx.json"
    
    # Check if voice files already exist
    if [ -f "$VOICE_ONNX" ] && [ -f "$VOICE_JSON" ]; then
        print_success "Voice files already exist"
        return 0
    fi
    
    print_info "Downloading voice files (this may take a few minutes)..."
    
    # Download ONNX file
    print_info "Downloading $VOICE_NAME.onnx..."
    if ! wget -q --show-progress -O "$VOICE_ONNX" "$VOICE_URL"; then
        print_error "Failed to download voice file"
        print_info "Trying with curl..."
        if ! curl -L --progress-bar -o "$VOICE_ONNX" "$VOICE_URL"; then
            print_error "Cannot download voice file. Please check your internet connection."
            print_info "You can manually download voices from:"
            print_info "https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/en"
            return 1
        fi
    fi
    
    # Download JSON file
    print_info "Downloading $VOICE_NAME.onnx.json..."
    if ! wget -q --show-progress -O "$VOICE_JSON" "$VOICE_JSON_URL"; then
        print_error "Failed to download JSON file"
        print_info "Trying with curl..."
        curl -L --progress-bar -o "$VOICE_JSON" "$VOICE_JSON_URL"
    fi
    
    # Verify downloads
    if [ -f "$VOICE_ONNX" ] && [ -f "$VOICE_JSON" ]; then
        ONNX_SIZE=$(du -h "$VOICE_ONNX" | cut -f1)
        print_success "Voice files downloaded successfully ($ONNX_SIZE)"
        return 0
    else
        print_error "Failed to download voice files"
        return 1
    fi
}

# Create desktop entry
create_desktop_entry() {
    print_info "Creating desktop entry..."
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Piper TTS
Comment=Offline Text-to-Speech Application
GenericName=Text-to-Speech
Keywords=TTS;Text-to-Speech;Speech;Audio;
Categories=AudioVideo;Audio;Utility;
Exec=$INSTALL_DIR/app/launcher.sh
Icon=$ICON_NAME
Terminal=false
StartupNotify=true
MimeType=text/plain;
Version=$APP_VERSION
EOF
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications"
    fi
    
    print_success "Desktop entry created"
}

# Create uninstall script
create_uninstaller() {
    print_info "Creating uninstall script..."
    
    cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
# Piper TTS Desktop - Uninstaller

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Uninstalling Piper TTS Desktop..."
echo "================================="

# Remove desktop entry
if [ -f "$HOME/.local/share/applications/piper-tts.desktop" ]; then
    rm "$HOME/.local/share/applications/piper-tts.desktop"
    echo "✓ Removed desktop entry"
fi

# Remove symlink
if [ -L "$HOME/.local/bin/piper-tts" ]; then
    rm "$HOME/.local/bin/piper-tts"
    echo "✓ Removed command line symlink"
fi

# Ask about removing voice files
read -p "Remove voice files (~120MB)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$HOME/.local/share/piper-tts" ]; then
        rm -rf "$HOME/.local/share/piper-tts"
        echo "✓ Removed all files"
    fi
else
    echo "Voice files kept at $HOME/.local/share/piper-tts/voices/"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
fi

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
EOF
    
    chmod +x "$INSTALL_DIR/uninstall.sh"
    
    print_success "Uninstall script created"
}

# Run post-install tests
post_install_tests() {
    print_info "Running post-installation tests..."
    
    # Test 1: Check if launcher script works
    if [ -x "$INSTALL_DIR/app/launcher.sh" ]; then
        print_success "Launcher script is executable"
    else
        print_error "Launcher script is not executable"
    fi
    
    # Test 2: Check if voice files exist
    if [ -f "$INSTALL_DIR/voices/$VOICE_NAME.onnx" ]; then
        VOICE_SIZE=$(du -h "$INSTALL_DIR/voices/$VOICE_NAME.onnx" | cut -f1)
        print_success "Voice file found ($VOICE_SIZE)"
    else
        print_warning "Voice file not found. You'll need to download it manually."
    fi
    
    # Test 3: Check virtual environment
    if [ -f "$INSTALL_DIR/venv/bin/activate" ]; then
        print_success "Virtual environment setup complete"
    else
        print_error "Virtual environment not found"
    fi
    
    print_success "Post-installation tests completed"
}

# Show completion message
show_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    INSTALLATION COMPLETE!              ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}🎤 Piper TTS Desktop is now installed!${NC}"
    echo ""
    echo -e "${YELLOW}📌 Installation Details:${NC}"
    echo "  Application:     $INSTALL_DIR/app/"
    echo "  Voices:          $INSTALL_DIR/voices/"
    echo "  Virtual Env:     $INSTALL_DIR/venv/"
    echo "  Desktop Entry:   $DESKTOP_FILE"
    echo ""
    echo -e "${YELLOW}🚀 How to launch:${NC}"
    echo "  1. Search for 'Piper TTS' in your Applications menu"
    echo "  2. Or run from terminal: $HOME/.local/bin/piper-tts"
    echo "  3. Or run directly: $INSTALL_DIR/app/launcher.sh"
    echo ""
    echo -e "${YELLOW}🔧 To uninstall:${NC}"
    echo "  Run: $INSTALL_DIR/uninstall.sh"
    echo ""
    echo -e "${YELLOW}🐛 Need help?${NC}"
    echo "  Run the test script: python3 $INSTALL_DIR/app/test_app.py"
    echo ""
}

# Main installation process
main() {
    print_header
    
    # Check if not running as root
    check_root
    
    # Check requirements
    check_requirements
    
    # Create directories
    create_directories
    
    # Install dependencies
    install_dependencies
    
    # Copy application
    copy_application
    
    # Download voices
    download_voices
    
    # Create desktop entry
    create_desktop_entry
    
    # Create uninstaller
    create_uninstaller
    
    # Run tests
    post_install_tests
    
    # Show completion message
    show_completion
}

# Run main function
main
