#!/usr/bin/env python3
# SIMPLE WORKING VERSION - BASIC FEATURES ONLY
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import time

class SimplePiperTTS:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper TTS - Simple")
        self.root.geometry("700x500")
        
        self.is_playing = False
        self.process = None
        
        # Check voices
        self.voices_dir = "~/.local/share/piper-tts/voices"
        self.voice_files = [
            "en_US-lessac-medium.onnx",
            "en_US-ryan-medium.onnx"
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        # Simple layout
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill='both', expand=True)
        
        # Text area
        ttk.Label(main, text="Enter text:").pack(anchor='w')
        self.text = scrolledtext.ScrolledText(main, height=10, wrap=tk.WORD)
        self.text.pack(fill='both', expand=True, pady=(0, 10))
        self.text.insert("1.0", "Test text for Piper TTS")
        
        # Controls
        controls = ttk.Frame(main)
        controls.pack(fill='x', pady=(0, 10))
        
        self.speak_btn = ttk.Button(controls, text="▶ Speak", command=self.speak)
        self.speak_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = ttk.Button(controls, text="⏹ Stop", command=self.stop, state='disabled')
        self.stop_btn.pack(side='left')
        
        # Status
        self.status = ttk.Label(main, text="Ready")
        self.status.pack(anchor='w')
        
    def speak(self):
        if self.is_playing:
            return
            
        text = self.text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No text", "Enter some text first")
            return
        
        # Use first available voice
        voice_path = os.path.expanduser("~/.local/share/piper-tts/voices/en_US-lessac-medium.onnx")
        if not os.path.exists(voice_path):
            voice_path = os.path.expanduser("~/.local/share/piper-tts/voices/en_US-ryan-medium.onnx")
        
        if not os.path.exists(voice_path):
            messagebox.showerror("No voices", "Download voice files to ~/.local/share/piper-tts/voices/")
            return
        
        self.is_playing = True
        self.speak_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status.config(text="Speaking...")
        
        thread = threading.Thread(target=self.run_tts, args=(text, voice_path), daemon=True)
        thread.start()
    
    def run_tts(self, text, voice_path):
        try:
            self.process = subprocess.Popen(
                ['piper', '--model', voice_path, '--output-raw'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            
            aplay = subprocess.Popen(
                ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw'],
                stdin=self.process.stdout
            )
            
            self.process.stdin.write(text.encode())
            self.process.stdin.close()
            self.process.wait()
            aplay.wait()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.reset)
    
    def stop(self):
        if self.process:
            self.process.terminate()
        self.reset()
    
    def reset(self):
        self.is_playing = False
        self.speak_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status.config(text="Ready")
    
    def on_close(self):
        self.stop()
        self.root.destroy()

# Run simple version
root = tk.Tk()
app = SimplePiperTTS(root)
root.protocol("WM_DELETE_WINDOW", app.on_close)
root.mainloop()
