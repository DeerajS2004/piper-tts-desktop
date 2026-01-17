#!/usr/bin/env python3
import os
import sys

print("Testing Piper TTS Installation...")
print("=" * 40)

# Check voice files
voices_path = os.path.expanduser("~/.local/share/piper-tts/voices")
print(f"Checking voices in: {voices_path}")
if os.path.exists(voices_path):
    onnx_files = [f for f in os.listdir(voices_path) if f.endswith('.onnx')]
    json_files = [f for f in os.listdir(voices_path) if f.endswith('.json')]
    print(f"Found {len(onnx_files)} .onnx files: {onnx_files}")
    print(f"Found {len(json_files)} .json files: {json_files}")
else:
    print("ERROR: Voices directory not found!")

# Check aplay
print("\nChecking aplay...")
import subprocess
result = subprocess.run(['which', 'aplay'], capture_output=True, text=True)
if result.returncode == 0:
    print(f"✓ aplay found at: {result.stdout.strip()}")
else:
    print("✗ aplay not found in PATH")

# Check Python modules
print("\nChecking Python modules...")
try:
    import tkinter
    print("✓ tkinter available")
except ImportError:
    print("✗ tkinter not available")

try:
    import piper
    print("✓ piper-tts available")
except ImportError:
    print("✗ piper-tts not available")

print("\n" + "=" * 40)
print("If you see any errors above, please fix them before running the app.")
print("\nTo run the app:")
print("1. Search for 'Piper TTS' in your Applications menu")
print("2. Or run: ~/.local/share/piper-tts/app/launcher.sh")
