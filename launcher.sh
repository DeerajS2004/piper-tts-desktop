#!/bin/bash
# Activate virtual environment and run Piper TTS
cd "$(dirname "$0")/.."
source venv/bin/activate
python app/piper_gui.py
