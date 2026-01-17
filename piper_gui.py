#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import time
import signal

class PiperTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper TTS")
        
        # Set window size and position
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Configure styles for modern look
        self.setup_styles()
        
        # Audio control
        self.piper_process = None
        self.aplay_process = None
        self.is_playing = False
        self.is_paused = False
        self.playback_thread = None
        
        # Position marking
        self.mark_position = None
        
        # Voice info
        self.voices = {
            "en_US-lessac-medium": "US Female",
            "en_US-ryan-medium": "US Male"
        }
        
        self.voice_files = {
            "en_US-lessac-medium": {
                "onnx": os.path.expanduser("~/.local/share/piper-tts/voices/en_US-lessac-medium.onnx"),
                "json": os.path.expanduser("~/.local/share/piper-tts/voices/en_US-lessac-medium.onnx.json")
            },
            "en_US-ryan-medium": {
                "onnx": os.path.expanduser("~/.local/share/piper-tts/voices/en_US-ryan-medium.onnx"),
                "json": os.path.expanduser("~/.local/share/piper-tts/voices/en_US-ryan-medium.onnx.json")
            }
        }
        
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
    def setup_styles(self):
        """Configure modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        self.colors = {
            'primary': '#2c3e50',      # Dark blue
            'secondary': '#3498db',    # Light blue
            'accent': '#e74c3c',       # Red for stop
            'success': '#27ae60',      # Green for play
            'warning': '#f39c12',      # Orange/yellow
            'light': '#ecf0f1',        # Light gray
            'dark': '#2c3e50',         # Dark gray
            'text': '#34495e',         # Text color
            'bg': '#f5f7fa',           # Background
            'toolbar': '#ffffff',      # Toolbar background
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Configure frame styles
        style.configure('Toolbar.TFrame', background=self.colors['toolbar'])
        style.configure('Card.TFrame', background='white', relief='solid', borderwidth=1)
        
        # Configure label styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 14, 'bold'),
                       background=self.colors['toolbar'],
                       foreground=self.colors['primary'])
        
        style.configure('Stats.TLabel',
                       font=('Segoe UI', 9),
                       foreground='#666666')
        
        # Configure button styles
        style.configure('Toolbar.TButton',
                       font=('Segoe UI', 9),
                       padding=6,
                       background=self.colors['light'],
                       foreground=self.colors['text'])
        
        style.map('Toolbar.TButton',
                 background=[('active', self.colors['secondary']),
                           ('disabled', '#bdc3c7')])
        
        style.configure('Play.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=8,
                       background=self.colors['success'],
                       foreground='white')
        
        style.configure('Pause.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=8,
                       background=self.colors['warning'],
                       foreground='white')
        
        style.configure('Stop.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=8,
                       background=self.colors['accent'],
                       foreground='white')
        
        style.configure('FromMark.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=8,
                       background=self.colors['secondary'],
                       foreground='white')
        
        # Configure combobox
        style.configure('Toolbar.TCombobox',
                       font=('Segoe UI', 9),
                       padding=3)
        
        # Configure scale (slider)
        style.configure('Toolbar.Horizontal.TScale',
                       background=self.colors['toolbar'])
    
    def setup_ui(self):
        """Setup the streamlined user interface"""
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill='both', expand=True)
        
        # ========== TOP TOOLBAR ==========
        toolbar = ttk.Frame(main_container, style='Toolbar.TFrame', padding="10")
        toolbar.pack(fill='x', pady=(0, 15))
        
        # Title
        title_label = ttk.Label(toolbar, 
                               text="🎤 PIPER TTS", 
                               style='Title.TLabel')
        title_label.pack(side='left', padx=(0, 30))
        
        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side='left', padx=10, fill='y')
        
        # ========== SETTINGS SECTION ==========
        settings_frame = ttk.Frame(toolbar)
        settings_frame.pack(side='left', padx=(0, 20))
        
        # Voice Selection
        voice_frame = ttk.Frame(settings_frame)
        voice_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(voice_frame, text="Voice:", font=('Segoe UI', 9)).pack(anchor='w')
        self.voice_var = tk.StringVar(value=list(self.voices.values())[0])
        self.voice_combo = ttk.Combobox(voice_frame, 
                                       textvariable=self.voice_var,
                                       values=list(self.voices.values()),
                                       state="readonly",
                                       width=12,
                                       style='Toolbar.TCombobox')
        self.voice_combo.pack(pady=(2, 0))
        
        # Speed Control
        speed_frame = ttk.Frame(settings_frame)
        speed_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(speed_frame, text="Speed:", font=('Segoe UI', 9)).pack(anchor='w')
        
        speed_controls = ttk.Frame(speed_frame)
        speed_controls.pack(pady=(2, 0))
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_slider = ttk.Scale(speed_controls, 
                                     from_=0.5, to=2.0, 
                                     variable=self.speed_var,
                                     orient='horizontal',
                                     length=80,
                                     style='Toolbar.Horizontal.TScale')
        self.speed_slider.pack(side='left')
        
        self.speed_label = ttk.Label(speed_controls, 
                                    text="1.0x",
                                    font=('Segoe UI', 9),
                                    width=4)
        self.speed_label.pack(side='left', padx=(5, 0))
        self.speed_var.trace_add("write", lambda *args: self.update_speed_label())
        
        # Position Marking
        mark_frame = ttk.Frame(settings_frame)
        mark_frame.pack(side='left', padx=(0, 15))
        
        ttk.Label(mark_frame, text="Position:", font=('Segoe UI', 9)).pack(anchor='w')
        
        mark_buttons = ttk.Frame(mark_frame)
        mark_buttons.pack(pady=(2, 0))
        
        self.mark_button = ttk.Button(mark_buttons,
                                     text="📍 Mark",
                                     style='Toolbar.TButton',
                                     command=self.mark_position_func,
                                     width=6)
        self.mark_button.pack(side='left', padx=(0, 3))
        
        self.jump_mark_button = ttk.Button(mark_buttons,
                                          text="↪️ Jump",
                                          style='Toolbar.TButton',
                                          command=self.jump_to_mark,
                                          state='disabled',
                                          width=6)
        self.jump_mark_button.pack(side='left')
        
        # Clear All
        clear_frame = ttk.Frame(settings_frame)
        clear_frame.pack(side='left')
        
        ttk.Label(clear_frame, text="Text:", font=('Segoe UI', 9)).pack(anchor='w')
        
        self.clear_button = ttk.Button(clear_frame,
                                      text="🗑️ Clear",
                                      style='Toolbar.TButton',
                                      command=self.clear_all_text,
                                      width=8)
        self.clear_button.pack(pady=(2, 0))
        
        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side='left', padx=10, fill='y')
        
        # ========== PLAYBACK CONTROLS ==========
        playback_frame = ttk.Frame(toolbar)
        playback_frame.pack(side='left', padx=(0, 10))
        
        ttk.Label(playback_frame, text="Playback:", font=('Segoe UI', 9)).pack(anchor='w')
        
        playback_buttons = ttk.Frame(playback_frame)
        playback_buttons.pack(pady=(2, 0))
        
        self.speak_button = ttk.Button(playback_buttons,
                                      text="▶ Speak",
                                      style='Play.TButton',
                                      command=self.speak,
                                      width=8)
        self.speak_button.pack(side='left', padx=(0, 5))
        
        self.pause_button = ttk.Button(playback_buttons,
                                      text="⏸ Pause",
                                      style='Pause.TButton',
                                      command=self.pause_speech,
                                      state='disabled',
                                      width=8)
        self.pause_button.pack(side='left', padx=(0, 5))
        
        self.stop_button = ttk.Button(playback_buttons,
                                     text="⏹ Stop",
                                     style='Stop.TButton',
                                     command=self.stop_speech,
                                     state='disabled',
                                     width=8)
        self.stop_button.pack(side='left', padx=(0, 5))
        
        self.speak_from_mark_button = ttk.Button(playback_buttons,
                                                text="▶ From Mark",
                                                style='FromMark.TButton',
                                                command=self.speak_from_mark,
                                                state='disabled',
                                                width=10)
        self.speak_from_mark_button.pack(side='left')
        
        # Help button on the right
        help_button = ttk.Button(toolbar,
                                text="❓ Help",
                                style='Toolbar.TButton',
                                command=self.show_shortcuts)
        help_button.pack(side='right', padx=(10, 0))
        
        # ========== TEXT INPUT AREA ==========
        text_card = ttk.Frame(main_container, style='Card.TFrame', padding="15")
        text_card.pack(fill='both', expand=True)
        
        # Text stats at top of text area
        stats_frame = ttk.Frame(text_card)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame,
                                    text="Characters: 0  |  Words: 0  |  Line: 1",
                                    style='Stats.TLabel')
        self.stats_label.pack(side='left')
        
        # Status indicator
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(stats_frame,
                                textvariable=self.status_var,
                                font=('Segoe UI', 9),
                                foreground=self.colors['secondary'])
        status_label.pack(side='right')
        
        # Text widget with scrollbars
        text_container = ttk.Frame(text_card)
        text_container.pack(fill='both', expand=True)
        
        self.text_input = tk.Text(text_container,
                                  wrap=tk.WORD,
                                  font=('Segoe UI', 11),
                                  relief='flat',
                                  bg='white',
                                  padx=10,
                                  pady=10,
                                  undo=True,
                                  maxundo=100)
        
        # Configure text tags for highlighting
        self.text_input.tag_config("current_line", background="#e8f4f8")
        self.text_input.tag_config("marked", background="#fff3cd")
        
        # Add scrollbars
        text_scroll_y = ttk.Scrollbar(text_container, orient='vertical', command=self.text_input.yview)
        text_scroll_x = ttk.Scrollbar(text_container, orient='horizontal', command=self.text_input.xview)
        self.text_input.configure(yscrollcommand=text_scroll_y.set, xscrollcommand=text_scroll_x.set)
        
        # Grid layout for text widget and scrollbars
        self.text_input.grid(row=0, column=0, sticky='nsew')
        text_scroll_y.grid(row=0, column=1, sticky='ns')
        text_scroll_x.grid(row=1, column=0, sticky='ew')
        
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.text_input.bind('<KeyRelease>', self.on_text_change)
        self.text_input.bind('<ButtonRelease-1>', self.update_line_info)
        self.text_input.bind('<KeyRelease>', lambda e: self.update_line_info())
        
        # Add sample text
        self.text_input.insert("1.0", """🎯 PIPER TTS - Streamlined Interface

All controls are now in the top toolbar for easy access:

TOOLBAR LAYOUT:
┌─────────────────────────────────────────────────────────────┐
│ VOICE: [US Female ▼]  SPEED: [━━━━━━━ 1.0x]  POSITION: [📍 Mark] [↪ Jump]  TEXT: [🗑 Clear]  │
│ PLAYBACK: [▶ Speak] [⏸ Pause] [⏹ Stop] [▶ From Mark]                                      │
└─────────────────────────────────────────────────────────────┘

HOW TO USE:
1. Type or paste your text below
2. Select voice and adjust speed as needed
3. Use "📍 Mark" to set a position to return to
4. Click "▶ Speak" to start reading
5. Use "▶ From Mark" to read from your marked position
6. Control playback with Pause/Stop buttons

KEYBOARD SHORTCUTS:
• Ctrl+Enter: Speak from beginning
• Ctrl+Shift+Enter: Speak from marked position
• Space: Pause/Resume (when playing)
• Escape: Stop playback
• Ctrl+M: Mark position
• Ctrl+J: Jump to mark
• Ctrl+A: Select all text
• Ctrl+Z/Y: Undo/Redo

Try it now! Type your text below and click "▶ Speak".""")
        
        self.update_stats()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-a>', self.select_all_text)
        self.root.bind('<Control-A>', self.select_all_text)
        self.root.bind('<Control-z>', lambda e: self.undo_text())
        self.root.bind('<Control-Z>', lambda e: self.undo_text())
        self.root.bind('<Control-y>', lambda e: self.redo_text())
        self.root.bind('<Control-Y>', lambda e: self.redo_text())
        self.root.bind('<Escape>', lambda e: self.stop_speech())
        self.root.bind('<Control-Return>', lambda e: self.speak())
        self.root.bind('<Control-Shift-Return>', lambda e: self.speak_from_mark())
        self.root.bind('<space>', lambda e: self.pause_speech() if self.is_playing else None)
        self.root.bind('<Control-m>', lambda e: self.mark_position_func())
        self.root.bind('<Control-M>', lambda e: self.mark_position_func())
        self.root.bind('<Control-j>', lambda e: self.jump_to_mark())
        self.root.bind('<Control-J>', lambda e: self.jump_to_mark())
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts = """
        🔊 PLAYBACK CONTROLS:
        Ctrl+Enter      - Speak from beginning
        Ctrl+Shift+Enter - Speak from marked position
        Space           - Pause/Resume (when playing)
        Escape          - Stop playback
        
        📍 POSITION NAVIGATION:
        Ctrl+M  - Mark current position
        Ctrl+J  - Jump to marked position
        
        📝 TEXT EDITING:
        Ctrl+A  - Select All
        Ctrl+Z  - Undo
        Ctrl+Y  - Redo
        Ctrl+C  - Copy
        Ctrl+V  - Paste
        Ctrl+X  - Cut
        
        🗑️  TEXT MANAGEMENT:
        Delete      - Remove selected text
        Backspace   - Delete character
        """
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def on_text_change(self, event=None):
        self.update_stats()
    
    def update_stats(self):
        """Update character, word, and line counts"""
        text = self.text_input.get("1.0", tk.END).strip()
        
        # Character count
        char_count = len(text)
        
        # Word count
        words = len(text.split()) if text else 0
        
        # Line count (current line)
        try:
            cursor_pos = self.text_input.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
        except:
            line_num = 1
        
        # Update stats label
        self.stats_label.config(text=f"Characters: {char_count:,}  |  Words: {words:,}  |  Line: {line_num}")
    
    def update_line_info(self, event=None):
        """Update current line highlighting"""
        try:
            # Remove previous line highlight
            self.text_input.tag_remove("current_line", "1.0", tk.END)
            
            # Get current line
            cursor_pos = self.text_input.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
            
            # Highlight current line
            self.text_input.tag_add("current_line", f"{line_num}.0", f"{line_num}.end+1c")
            
            # Update stats
            self.update_stats()
        except:
            pass
    
    def update_speed_label(self, event=None):
        speed = self.speed_var.get()
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def get_selected_voice_key(self):
        display_name = self.voice_var.get()
        for key, name in self.voices.items():
            if name == display_name:
                return key
        return list(self.voices.keys())[0]
    
    def speak(self, from_marked_position=False):
        """Start speaking text"""
        if self.is_playing:
            self.stop_speech()
            time.sleep(0.2)
        
        # Get full text
        full_text = self.text_input.get("1.0", tk.END).strip()
        
        # If speaking from marked position, get text from mark
        text_to_speak = full_text
        start_position_info = "Speaking..."
        
        if from_marked_position and self.mark_position:
            # Get text from marked position onward
            text_to_speak = self.text_input.get(self.mark_position, tk.END).strip()
            if not text_to_speak:
                messagebox.showinfo("No text", "No text to speak from marked position.")
                return
            start_position_info = "Speaking from mark..."
            
            # Show where we're starting from
            line, col = map(int, self.mark_position.split('.'))
            self.status_var.set(f"From line {line}")
        else:
            # Normal speak from beginning
            if not text_to_speak:
                messagebox.showwarning("No text", "Please enter some text to speak.")
                return
        
        voice_key = self.get_selected_voice_key()
        voice_info = self.voice_files.get(voice_key)
        
        if not voice_info or not os.path.exists(voice_info["onnx"]):
            messagebox.showerror("Voice not found", f"Voice file not found: {voice_key}")
            return
        
        # Update UI
        self.status_var.set(start_position_info)
        self.speak_button.config(state='disabled')
        self.speak_from_mark_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        self.is_playing = True
        self.is_paused = False
        
        # Highlight where we're reading from
        self.text_input.tag_remove("marked", "1.0", tk.END)
        if from_marked_position and self.mark_position:
            self.text_input.tag_add("marked", self.mark_position)
        
        # Start playback thread
        self.playback_thread = threading.Thread(
            target=self.run_piper, 
            args=(text_to_speak, voice_info), 
            daemon=True
        )
        self.playback_thread.start()
    
    def speak_from_mark(self):
        """Speak starting from marked position"""
        if not self.mark_position:
            messagebox.showinfo("No Mark", "Please mark a position first using '📍 Mark' button.")
            return
        self.speak(from_marked_position=True)
    
    def run_piper(self, text, voice_info):
        """Run piper with process control"""
        try:
            speed = self.speed_var.get()
            
            # Build command
            cmd = ['piper', '--model', voice_info["onnx"], '--output-raw']
            
            if speed != 1.0:
                cmd.extend(['--length_scale', str(1.0/speed)])
            
            # Create piper process
            self.piper_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Create aplay process
            self.aplay_process = subprocess.Popen(
                ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-c', '1'],
                stdin=self.piper_process.stdout,
                stderr=subprocess.PIPE
            )
            
            # Send text
            self.piper_process.stdin.write(text.encode())
            self.piper_process.stdin.close()
            
            # Monitor playback
            while True:
                if not self.is_playing:
                    break
                
                if self.is_paused:
                    # Pause aplay
                    if self.aplay_process:
                        self.aplay_process.send_signal(signal.SIGSTOP)
                    while self.is_paused and self.is_playing:
                        time.sleep(0.1)
                    # Resume aplay
                    if self.aplay_process and self.aplay_process.poll() is None:
                        self.aplay_process.send_signal(signal.SIGCONT)
                
                # Check if processes are done
                piper_done = self.piper_process.poll() is not None
                aplay_done = self.aplay_process.poll() is not None
                
                if piper_done and aplay_done:
                    break
                
                time.sleep(0.1)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to speak: {str(e)}"))
        finally:
            self.cleanup_processes()
            self.root.after(0, self.reset_ui)
    
    def pause_speech(self):
        """Pause or resume speech"""
        if not self.is_playing:
            return
        
        if not self.is_paused:
            # Pause
            self.is_paused = True
            self.pause_button.config(text="▶ Resume")
            self.status_var.set("Paused")
        else:
            # Resume
            self.is_paused = False
            self.pause_button.config(text="⏸ Pause")
            self.status_var.set("Resuming...")
    
    def stop_speech(self):
        """Stop speech playback"""
        self.is_playing = False
        self.is_paused = False
        self.cleanup_processes()
        self.reset_ui()
        self.status_var.set("Stopped")
    
    def cleanup_processes(self):
        """Clean up running processes"""
        if self.aplay_process:
            try:
                self.aplay_process.terminate()
                time.sleep(0.1)
                if self.aplay_process.poll() is None:
                    self.aplay_process.kill()
            except:
                pass
            finally:
                self.aplay_process = None
        
        if self.piper_process:
            try:
                self.piper_process.terminate()
                time.sleep(0.1)
                if self.piper_process.poll() is None:
                    self.piper_process.kill()
            except:
                pass
            finally:
                self.piper_process = None
    
    def reset_ui(self):
        """Reset UI state"""
        self.is_playing = False
        self.is_paused = False
        self.speak_button.config(state='normal')
        self.speak_from_mark_button.config(state='normal' if self.mark_position else 'disabled')
        self.pause_button.config(state='disabled', text="⏸ Pause")
        self.stop_button.config(state='disabled')
        
        # Clear highlighting
        self.text_input.tag_remove("marked", "1.0", tk.END)
        
        if not self.is_playing:
            self.status_var.set("Ready")
    
    def mark_position_func(self):
        """Mark current cursor position"""
        try:
            self.mark_position = self.text_input.index(tk.INSERT)
            self.speak_from_mark_button.config(state='normal')
            self.jump_mark_button.config(state='normal')
            
            # Highlight marked position
            self.text_input.tag_remove("marked", "1.0", tk.END)
            self.text_input.tag_add("marked", self.mark_position)
            
            line, col = map(int, self.mark_position.split('.'))
            self.status_var.set(f"Marked line {line}")
        except:
            pass
    
    def jump_to_mark(self):
        """Jump cursor to marked position"""
        if self.mark_position:
            self.text_input.mark_set(tk.INSERT, self.mark_position)
            self.text_input.see(self.mark_position)
            self.text_input.focus()
            
            # Highlight it again
            self.text_input.tag_remove("marked", "1.0", tk.END)
            self.text_input.tag_add("marked", self.mark_position)
            
            line, col = map(int, self.mark_position.split('.'))
            self.status_var.set(f"Jumped to line {line}")
    
    def clear_all_text(self):
        """Clear all text from input"""
        if self.text_input.get("1.0", "end-1c").strip():
            self.text_input.delete("1.0", tk.END)
            self.text_input.focus()
            self.update_stats()
            # Clear mark when text is cleared
            self.mark_position = None
            self.speak_from_mark_button.config(state='disabled')
            self.jump_mark_button.config(state='disabled')
            self.status_var.set("Text cleared")
    
    # Keyboard shortcut functions
    def select_all_text(self, event=None):
        self.text_input.tag_add('sel', '1.0', 'end')
        self.text_input.focus()
        return "break"
    
    def undo_text(self, event=None):
        try:
            self.text_input.edit_undo()
        except:
            pass
        return "break"
    
    def redo_text(self, event=None):
        try:
            self.text_input.edit_redo()
        except:
            pass
        return "break"
    
    def on_closing(self):
        """Clean shutdown"""
        self.stop_speech()
        time.sleep(0.2)
        self.cleanup_processes()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = PiperTTSApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
