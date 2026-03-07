# Piper TTS Desktop

A fully offline, privacy-first Text-to-Speech desktop app built on the [Piper TTS](https://github.com/rhasspy/piper) engine. No internet connection required after setup — all synthesis runs locally.

---

## Features

- **100% Offline** — No cloud, no API keys, no data leaves your machine
- **Multiple Voices** — Switch between any downloaded Piper voice model (en_US, en_GB, Spanish, German, French, Hindi, and more)
- **Speed Control** — Adjustable playback speed from 0.5× to 2.0×
- **Position Marking** — Mark any line and resume playback or jump back to it anytime
- **Export to WAV** — Save speech as a WAV audio file
- **Dark / Light Mode** — Toggle between themes
- **Font Size Control** — Resize text in the editor (8pt – 24pt)
- **Keyboard Shortcuts** — Full keyboard support for hands-free use
- **Desktop Integration** — Installs as an app menu entry on Linux desktops

---

## Requirements

- Linux (Ubuntu / Debian-based recommended)
- Python 3.8+
- `aplay` (from `alsa-utils`)
- `tkinter` (usually bundled with Python)
- At least one Piper voice model (`.onnx` + `.onnx.json`) — the installer downloads one automatically

---

## Installation

```bash
git clone https://github.com/DeerajS2004/piper-tts-desktop.git
cd piper-tts-desktop

chmod +x scripts/install.sh
./scripts/install.sh
```

The installer will:
- Check and install dependencies (`aplay`, `tkinter`, `pip`)
- Create a Python virtual environment
- Install `piper-tts` via pip
- Download the default voice (`en_US-lessac-medium`, ~42 MB)
- Create a desktop app menu entry
- Add a `piper-tts` command to `~/.local/bin`

---

## Usage

**From the app menu:** Search for "Piper TTS"

**From terminal:**
```bash
piper-tts
# or directly:
~/.local/share/piper-tts/app/launcher.sh
```

---

## Adding More Voices

Download any voice from the [Piper voice samples page](https://rhasspy.github.io/piper-samples/). You need two files per voice:

```
<voice-name>.onnx
<voice-name>.onnx.json
```

Place both in `~/.local/share/piper-tts/voices/` and restart the app. The new voice will appear in the dropdown automatically.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Speak from beginning |
| `Ctrl+Shift+Enter` | Speak from marked position |
| `Space` | Pause / Resume (while playing) |
| `Escape` | Stop playback |
| `Ctrl+M` | Mark current cursor position |
| `Ctrl+J` | Jump to marked position |
| `Ctrl+E` | Export audio as WAV |
| `Ctrl+T` | Toggle dark / light mode |
| `Ctrl++` / `Ctrl+-` | Increase / decrease font size |
| `Ctrl+0` | Reset font size |
| `Ctrl+A` | Select all text |
| `Ctrl+Z` / `Ctrl+Y` | Undo / Redo |

---

## Uninstall

```bash
~/.local/share/piper-tts/uninstall.sh
```

You'll be asked whether to keep or delete the downloaded voice files.

---

## Project Structure

```
piper-tts-desktop/
├── app/
│   ├── piper_gui.py       # Main application
│   ├── piper-icon.png     # App icon
│   └── test_app.py        # Diagnostic/test script
├── scripts/
│   ├── install.sh         # Main installer
│   └── launcher.sh        # App launcher
├── .gitignore
├── LICENSE
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
