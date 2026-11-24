#!/usr/bin/env python3
"""Piper TTS Web Server — serves the HTML frontend and TTS API."""
import os, sys, wave, base64, threading, tempfile, re, subprocess, webbrowser
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory, Response
except ImportError:
    print("Flask not installed. Run: pip install flask")
    sys.exit(1)

# ─── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_BIN   = Path(sys.executable).parent
PIPER_BIN  = str(VENV_BIN / 'piper')

def find_voices_dir():
    candidates = [
        os.environ.get('PIPER_VOICES_DIR', ''),
        str(SCRIPT_DIR.parent / 'voices'),
        str(Path.home() / '.local/share/piper-tts/voices'),
        '/usr/share/piper-tts/voices',
    ]
    for c in candidates:
        if c and Path(c).is_dir():
            return str(c)
    return str(SCRIPT_DIR.parent / 'voices')

VOICES_DIR = find_voices_dir()
PORT = int(os.environ.get('PIPER_PORT', 5000))

# ─── Pause durations from benchmarks (seconds at 1× speed) ─────────────────
EN_PAUSES = {'.': 0.50, ',': 0.27, ';': 0.78, ':': 0.42,
             '!': 0.33, '?': 0.46, '\n': 0.35, '…': -0.16}
JA_PAUSES = {'。': 0.72, '！': 0.65, '？': 0.91, '、': 0.0,
             '\n': 0.70, '…': -0.08}

# Baseline CPM at 1× (from benchmarks on en_US-lessac-medium / ja_JP-hi_fi_captain)
LANG_CPM = {'en': 1160, 'ja': 303}

# ─── Flask app ──────────────────────────────────────────────────────────────
app = Flask(__name__)

LANG_INFO = {
    'en_US': ('English (US)', 'en', '🇺🇸'),
    'en_GB': ('English (UK)', 'en', '🇬🇧'),
    'ja_JP': ('Japanese',    'ja', '🇯🇵'),
}

@app.route('/')
def index():
    return send_from_directory(str(SCRIPT_DIR), 'index.html')

@app.route('/api/voices')
def get_voices():
    voices = []
    vdir = Path(VOICES_DIR)
    if vdir.is_dir():
        for f in sorted(vdir.iterdir()):
            if f.suffix == '.onnx':
                name  = f.stem
                parts = name.split('-')
                locale = parts[0]
                label_en, lang, flag = LANG_INFO.get(locale, (locale, 'en', ''))
                speaker = ' '.join(p.capitalize() for p in parts[1:])
                voices.append({
                    'id':     name,
                    'onnx':   str(f),
                    'lang':   lang,
                    'label':  f"{flag} {label_en} — {speaker}".strip(' —'),
                    'cpm_1x': LANG_CPM.get(lang, 1160),
                })
    return jsonify(voices)

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    data       = request.json or {}
    full_text  = data.get('text', '')
    voice_id   = data.get('voice', '')
    speed      = float(data.get('speed', 1.0))
    start_char = int(data.get('start_char', 0))
    lang       = data.get('lang', 'en')

    text = full_text.strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    onnx = Path(VOICES_DIR) / f'{voice_id}.onnx'
    if not onnx.exists():
        return jsonify({'error': f'Voice not found: {voice_id}'}), 404

    # Slice from start_char
    speak_text = text[start_char:] if 0 < start_char < len(text) else text
    if not speak_text.strip():
        return jsonify({'error': 'Nothing to speak from that position'}), 400

    try:
        wav_bytes, duration = _run_piper(str(onnx), speak_text, speed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    timings = _estimate_timing(speak_text, duration, speed, lang, offset=start_char)
    cpm     = round(len(speak_text) / (duration / 60)) if duration > 0 else 0

    return jsonify({
        'audio':    base64.b64encode(wav_bytes).decode(),
        'duration': round(duration, 3),
        'timings':  timings,
        'cpm':      cpm,
    })

@app.route('/api/export', methods=['POST'])
def export_audio():
    data     = request.json or {}
    text     = data.get('text', '').strip()
    voice_id = data.get('voice', '')
    speed    = float(data.get('speed', 1.0))

    if not text:
        return jsonify({'error': 'No text'}), 400
    onnx = Path(VOICES_DIR) / f'{voice_id}.onnx'
    if not onnx.exists():
        return jsonify({'error': 'Voice not found'}), 404

    try:
        wav_bytes, _ = _run_piper(str(onnx), text, speed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return Response(wav_bytes, mimetype='audio/wav',
        headers={'Content-Disposition': 'attachment; filename="piper-tts.wav"'})

# ─── Helpers ────────────────────────────────────────────────────────────────
def _run_piper(onnx: str, text: str, speed: float):
    fd, wav_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    try:
        cmd = [PIPER_BIN, '--model', onnx, '--output_file', wav_path]
        if speed != 1.0:
            cmd += ['--length_scale', str(round(1.0 / speed, 4))]
        r = subprocess.run(cmd, input=text.encode('utf-8'),
                           capture_output=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(
                r.stderr.decode('utf-8', errors='replace').strip() or 'piper failed')
        wav_bytes = Path(wav_path).read_bytes()
        with wave.open(wav_path, 'r') as w:
            duration = w.getnframes() / w.getframerate()
        return wav_bytes, duration
    finally:
        try: os.unlink(wav_path)
        except: pass

def _estimate_timing(text: str, total_dur: float, speed: float,
                     lang: str, offset: int = 0):
    """Estimate per-word timing using character count + benchmark pause data."""
    is_ja  = (lang == 'ja')
    pauses = JA_PAUSES if is_ja else EN_PAUSES
    tokens = _tokenize(text, is_ja, pauses, offset)
    if not tokens:
        return []

    total_chars = sum(t['chars'] for t in tokens)
    # Pauses scale inversely with speed; negative pauses (…) are ignored in total
    total_pause = sum(max(0.0, t['pause']) / speed for t in tokens)
    speech_time = max(0.01, total_dur - total_pause)
    tpc = speech_time / max(total_chars, 1)   # time per speech-character

    result, cur = [], 0.0
    for i, tok in enumerate(tokens):
        dur = tok['chars'] * tpc + tok['pause'] / speed
        dur = max(0.0, dur)
        result.append({
            'idx':        i,
            'text':       tok['text'],
            'start_char': tok['sc'],
            'end_char':   tok['ec'],
            'start_time': round(cur, 4),
            'end_time':   round(cur + dur, 4),
        })
        cur += dur
    return result

def _tokenize(text: str, is_ja: bool, pauses: dict, offset: int):
    toks = []
    if is_ja:
        for i, ch in enumerate(text):
            if ch in ' \t\r':
                continue
            toks.append({
                'text': ch, 'sc': offset + i, 'ec': offset + i + 1,
                'chars': 0 if ch in pauses else 1,
                'pause': pauses.get(ch, 0),
            })
    else:
        for m in re.finditer(r'\S+', text):
            w  = m.group()
            sc = offset + m.start()
            ec = offset + m.end()
            sp = max(len(re.sub(r"[^\w']", '', w)), 1)
            pause = sum(pauses.get(c, 0) for c in w if c in pauses)
            after = text[m.end(): m.end() + 1]
            if after == '\n':
                pause += pauses.get('\n', 0)
            toks.append({'text': w, 'sc': sc, 'ec': ec, 'chars': sp, 'pause': pause})
    return toks

if __name__ == '__main__':
    print(f'\n🎤 Piper TTS starting → http://localhost:{PORT}')
    print(f'   Voices : {VOICES_DIR}')
    print(f'   Piper  : {PIPER_BIN}')
    if not Path(PIPER_BIN).exists():
        print('   ⚠️  piper binary not found!')
    threading.Timer(0.9, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)
