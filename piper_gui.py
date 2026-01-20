#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import time
import signal

class PiperTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper TTS")
        
        # Set window icon
        self.set_window_icon()
        
        # Set window size
        self.root.geometry("1000x750")
        
        # Font size tracking
        self.font_size = 11
        self.min_font_size = 8
        self.max_font_size = 24
        
        # Configure styles
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
        self.voices = {}
        self.voice_files = {}
        
        # Theme
        self.is_dark_mode = False
        
        # Scrollbar visibility
        self.scrollbars_visible = False
        
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        self.scan_installed_voices()
    
    def set_window_icon(self):
        """Set custom window icon if available"""
        try:
            # Look for icon in multiple locations
            icon_locations = [
                os.path.join(os.path.dirname(__file__), "piper-icon.png"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "piper-icon.png"),
                os.path.expanduser("~/.local/share/piper-tts/app/piper-icon.png"),
                "/usr/share/pixmaps/piper-tts.png",
                "piper-icon.png"
            ]
            
            for icon_path in icon_locations:
                if os.path.exists(icon_path):
                    # Load the icon
                    icon_img = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, icon_img)
                    self.icon_img = icon_img  # Keep reference to prevent garbage collection
                    print(f"✓ Icon loaded from: {icon_path}")
                    break
            else:
                print("ℹ️ Icon not found. To add a custom icon, place 'piper-icon.png' in the app folder.")
        except Exception as e:
            print(f"⚠️ Could not load icon: {e}")
    
    def setup_styles(self):
        """Configure modern ttk styles with theme support"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Light mode colors
        self.light_colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'dark': '#2c3e50',
            'text': '#34495e',
            'bg': '#f5f7fa',
            'toolbar': '#ffffff',
            'card': '#ffffff',
            'input_bg': '#ffffff',
            'input_fg': '#000000',
            'settings_bg': '#f8f9fa',
            'playback_bg': '#e3f2fd',
            'current_line': '#e8f4f8',
            'marked': '#fff3cd',
            'scrollbar_trough': '#f0f0f0',
            'scrollbar_slider': '#c0c0c0',
            'scrollbar_slider_hover': '#a0a0a0'
        }
        
        # Dark mode colors
        self.dark_colors = {
            'primary': '#3498db',
            'secondary': '#1abc9c',
            'accent': '#e74c3c',
            'success': '#2ecc71',
            'warning': "#D7DA3A",
            'light': "#ffffff",
            'dark': "#000000",
            'text': "#000000",
            'bg': "#1a1a1a",
            'toolbar': "#ffffff",
            'card': "#2d2d2d",
            'input_bg': "#000000",
            'input_fg': '#ffffff',
            'settings_bg': "#FFFFFF",
            'playback_bg': '#1e3a5f',
            'current_line': '#2d4a6e',
            'marked': '#5d4a1e',
            'scrollbar_trough': '#3d3d3d',
            'scrollbar_slider': '#666666',
            'scrollbar_slider_hover': '#888888'
        }
        
        # Start with light mode
        self.colors = self.light_colors
        self.apply_theme()
    
    def apply_theme(self):
        """Apply current theme colors to the UI"""
        style = ttk.Style()
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Configure frame styles
        style.configure('Toolbar.TFrame', background=self.colors['toolbar'])
        style.configure('Card.TFrame', background=self.colors['card'])
        
        # Configure label styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 14, 'bold'),
                       background=self.colors['toolbar'],
                       foreground=self.colors['primary'])
        
        style.configure('Stats.TLabel',
                       font=('Segoe UI', 9),
                       foreground=self.colors['text'])
        
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
        
        style.configure('Export.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=8,
                       background='#9b59b6',
                       foreground='white')
        
        # Configure combobox
        style.configure('Toolbar.TCombobox',
                       font=('Segoe UI', 9),
                       padding=3)
        
        # Configure scale (slider)
        style.configure('Toolbar.Horizontal.TScale',
                       background=self.colors['toolbar'])
        
        # Configure scrollbars
        self.configure_scrollbars()
        
        # Update text widget colors and font
        if hasattr(self, 'text_input'):
            self.update_text_widget_font()
            self.text_input.configure(
                bg=self.colors['input_bg'],
                fg=self.colors['input_fg'],
                insertbackground=self.colors['secondary']
            )
            
            # Update text tags
            self.text_input.tag_config("current_line", background=self.colors['current_line'])
            self.text_input.tag_config("marked", background=self.colors['marked'])
            
            # Update other UI elements
            if hasattr(self, 'settings_frame'):
                self.settings_frame.configure(bg=self.colors['settings_bg'])
                for child in self.settings_frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=self.colors['settings_bg'])
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Frame):
                                subchild.configure(bg=self.colors['settings_bg'])
            
            if hasattr(self, 'playback_frame'):
                self.playback_frame.configure(bg=self.colors['playback_bg'])
    
    def configure_scrollbars(self):
        """Configure scrollbar appearance"""
        style = ttk.Style()
        
        # Configure colors
        style.configure("Vertical.TScrollbar",
                       troughcolor=self.colors['scrollbar_trough'],
                       background=self.colors['scrollbar_slider'],
                       arrowcolor=self.colors['scrollbar_slider'],
                       bordercolor=self.colors['scrollbar_trough'],
                       darkcolor=self.colors['scrollbar_slider'],
                       lightcolor=self.colors['scrollbar_slider'])
        
        style.configure("Horizontal.TScrollbar",
                       troughcolor=self.colors['scrollbar_trough'],
                       background=self.colors['scrollbar_slider'],
                       arrowcolor=self.colors['scrollbar_slider'],
                       bordercolor=self.colors['scrollbar_trough'],
                       darkcolor=self.colors['scrollbar_slider'],
                       lightcolor=self.colors['scrollbar_slider'])
        
        # Map for hover effects
        style.map("Vertical.TScrollbar",
                 background=[('active', self.colors['scrollbar_slider_hover'])])
        style.map("Horizontal.TScrollbar",
                 background=[('active', self.colors['scrollbar_slider_hover'])])
    
    def update_text_widget_font(self):
        """Update the text widget font size"""
        font_family = 'Segoe UI'
        font_config = (font_family, self.font_size)
        self.text_input.configure(font=font_config)
    
    def change_font_size(self, delta):
        """Change font size by delta (+ for increase, - for decrease)"""
        new_size = self.font_size + delta
        
        # Apply bounds
        if self.min_font_size <= new_size <= self.max_font_size:
            self.font_size = new_size
            self.update_text_widget_font()
            self.status_var.set(f"Font size: {self.font_size}pt")
    
    def reset_font_size(self):
        """Reset font size to default"""
        self.font_size = 11
        self.update_text_widget_font()
        self.status_var.set(f"Font size reset to {self.font_size}pt")
    
    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.is_dark_mode = not self.is_dark_mode
        
        if self.is_dark_mode:
            self.colors = self.dark_colors
            if hasattr(self, 'theme_button'):
                self.theme_button.config(text="☀️ Light")
        else:
            self.colors = self.light_colors
            if hasattr(self, 'theme_button'):
                self.theme_button.config(text="🌙 Dark")
        
        self.apply_theme()
        self.check_scrollbar_visibility()
    
    def check_scrollbar_visibility(self):
        """Check if scrollbars should be visible"""
        if not hasattr(self, 'text_input'):
            return
        
        try:
            # Check vertical scroll
            text_content = self.text_input.get("1.0", "end-1c")
            self.text_input.update_idletasks()
            
            # Get text widget dimensions
            text_bbox = self.text_input.bbox("end-1c")
            
            # If there's no content or content fits, hide scrollbars
            if not text_content or (text_bbox and text_bbox[1] < self.text_input.winfo_height() - 20):
                self.hide_scrollbars()
            else:
                self.show_scrollbars()
                
            # Check horizontal scroll
            max_line_length = 0
            line_count = int(self.text_input.index('end-1c').split('.')[0])
            
            for i in range(1, line_count + 1):
                line = self.text_input.get(f"{i}.0", f"{i}.end")
                if len(line) > max_line_length:
                    max_line_length = len(line)
            
            # Rough estimate: average character width ~8 pixels
            if max_line_length * 8 < self.text_input.winfo_width() - 20:
                self.hide_horizontal_scrollbar()
            else:
                self.show_horizontal_scrollbar()
                
        except Exception as e:
            print(f"Scrollbar visibility check error: {e}")
            # Default to showing scrollbars on error
            self.show_scrollbars()
    
    def hide_scrollbars(self):
        """Hide scrollbars"""
        if hasattr(self, 'text_scroll_y') and self.scrollbars_visible:
            self.text_scroll_y.grid_remove()
            self.scrollbars_visible = False
    
    def show_scrollbars(self):
        """Show scrollbars"""
        if hasattr(self, 'text_scroll_y') and not self.scrollbars_visible:
            self.text_scroll_y.grid()
            self.scrollbars_visible = True
    
    def hide_horizontal_scrollbar(self):
        """Hide horizontal scrollbar"""
        if hasattr(self, 'text_scroll_x'):
            self.text_scroll_x.grid_remove()
    
    def show_horizontal_scrollbar(self):
        """Show horizontal scrollbar"""
        if hasattr(self, 'text_scroll_x'):
            self.text_scroll_x.grid()
    
    def scan_installed_voices(self):
        """Scan for installed voice files"""
        voices_dir = os.path.expanduser("~/.local/share/piper-tts/voices")
        
        self.voices = {}
        self.voice_files = {}
        
        if not os.path.exists(voices_dir):
            print("ℹ️ Voices directory not found")
            return
        
        for filename in os.listdir(voices_dir):
            if filename.endswith('.onnx'):
                voice_id = filename[:-5]  # Remove .onnx extension
                json_file = f"{voice_id}.onnx.json"
                
                onnx_path = os.path.join(voices_dir, filename)
                json_path = os.path.join(voices_dir, json_file)
                
                if os.path.exists(json_path):
                    # Simple display name
                    if "lessac" in voice_id.lower():
                        display_name = f"Lessac ({voice_id.split('-')[0]})"
                    elif "ryan" in voice_id.lower():
                        display_name = f"Ryan ({voice_id.split('-')[0]})"
                    else:
                        display_name = voice_id
                    
                    self.voices[voice_id] = display_name
                    self.voice_files[voice_id] = {
                        "onnx": onnx_path,
                        "json": json_path
                    }
        
        # Update combobox
        if hasattr(self, 'voice_combo'):
            current = self.voice_var.get()
            self.voice_combo['values'] = list(self.voices.values())
            
            if current in self.voices.values():
                self.voice_var.set(current)
            elif self.voices:
                self.voice_var.set(list(self.voices.values())[0])
            else:
                self.voice_var.set("No voices found")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True)
        
        # ========== TOP TOOLBAR ==========
        toolbar = ttk.Frame(main_container, style='Toolbar.TFrame')
        toolbar.pack(fill='x', pady=(0, 5))
        
        # Title
        title_label = ttk.Label(toolbar, 
                               text="🎤 PIPER TTS", 
                               style='Title.TLabel')
        title_label.pack(side='left', padx=10)
        
        # ========== SETTINGS SECTION ==========
        self.settings_frame = tk.Frame(toolbar, bg=self.colors['settings_bg'])
        self.settings_frame.pack(side='left', padx=20)
        
        # Voice Selection
        voice_frame = tk.Frame(self.settings_frame, bg=self.colors['settings_bg'])
        voice_frame.pack(side='left', padx=5)
        
        ttk.Label(voice_frame, text="Voice:", 
                 font=('Segoe UI', 9)).pack(anchor='w')
        
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(voice_frame, 
                                       textvariable=self.voice_var,
                                       values=[],
                                       state="readonly",
                                       width=15,
                                       style='Toolbar.TCombobox')
        self.voice_combo.pack(pady=(2, 0))
        
        # Speed Control
        speed_frame = tk.Frame(self.settings_frame, bg=self.colors['settings_bg'])
        speed_frame.pack(side='left', padx=5)
        
        ttk.Label(speed_frame, text="Speed:", 
                 font=('Segoe UI', 9)).pack(anchor='w')
        
        speed_controls = tk.Frame(speed_frame, bg=self.colors['settings_bg'])
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
        mark_frame = tk.Frame(self.settings_frame, bg=self.colors['settings_bg'])
        mark_frame.pack(side='left', padx=5)
        
        ttk.Label(mark_frame, text="Position:", 
                 font=('Segoe UI', 9)).pack(anchor='w')
        
        mark_buttons = tk.Frame(mark_frame, bg=self.colors['settings_bg'])
        mark_buttons.pack(pady=(2, 0))
        
        self.mark_button = ttk.Button(mark_buttons,
                                     text="📍 Mark",
                                     style='Toolbar.TButton',
                                     command=self.mark_position_func,
                                     width=8)
        self.mark_button.pack(side='left')
        
        self.jump_mark_button = ttk.Button(mark_buttons,
                                          text="↪️ Jump",
                                          style='Toolbar.TButton',
                                          command=self.jump_to_mark,
                                          state='disabled',
                                          width=8)
        self.jump_mark_button.pack(side='left', padx=(2, 0))
        
        # Clear All
        clear_frame = tk.Frame(self.settings_frame, bg=self.colors['settings_bg'])
        clear_frame.pack(side='left', padx=5)
        
        ttk.Label(clear_frame, text="Text:", 
                 font=('Segoe UI', 9)).pack(anchor='w')
        
        self.clear_button = ttk.Button(clear_frame,
                                      text="🗑️ Clear",
                                      style='Toolbar.TButton',
                                      command=self.clear_all_text,
                                      width=8)
        self.clear_button.pack(pady=(2, 0))
        
        # ========== PLAYBACK CONTROLS ==========
        self.playback_frame = tk.Frame(toolbar, bg=self.colors['playback_bg'])
        self.playback_frame.pack(side='left', padx=20)
        
        playback_buttons = tk.Frame(self.playback_frame, bg=self.colors['playback_bg'])
        playback_buttons.pack()
        
        self.speak_button = ttk.Button(playback_buttons,
                                      text="▶ Speak",
                                      style='Play.TButton',
                                      command=self.speak,
                                      width=8)
        self.speak_button.pack(side='left', padx=2)
        
        self.pause_button = ttk.Button(playback_buttons,
                                      text="⏸ Pause",
                                      style='Pause.TButton',
                                      command=self.pause_speech,
                                      state='disabled',
                                      width=8)
        self.pause_button.pack(side='left', padx=2)
        
        self.stop_button = ttk.Button(playback_buttons,
                                     text="⏹ Stop",
                                     style='Stop.TButton',
                                     command=self.stop_speech,
                                     state='disabled',
                                     width=8)
        self.stop_button.pack(side='left', padx=2)
        
        self.speak_from_mark_button = ttk.Button(playback_buttons,
                                                text="▶ From Mark",
                                                style='FromMark.TButton',
                                                command=self.speak_from_mark,
                                                state='disabled',
                                                width=10)
        self.speak_from_mark_button.pack(side='left', padx=2)
        
        self.export_button = ttk.Button(playback_buttons,
                                       text="💾 Export",
                                       style='Export.TButton',
                                       command=self.export_audio,
                                       width=8)
        self.export_button.pack(side='left', padx=2)
        
        # Theme toggle button
        self.theme_button = ttk.Button(toolbar,
                                      text="🌙 Dark",
                                      style='Toolbar.TButton',
                                      command=self.toggle_theme)
        self.theme_button.pack(side='right', padx=10)
        
        # Help button
        help_button = ttk.Button(toolbar,
                                text="❓ Help",
                                style='Toolbar.TButton',
                                command=self.show_shortcuts)
        help_button.pack(side='right', padx=10)
        
        # ========== TEXT INPUT AREA ==========
        text_card = ttk.Frame(main_container, style='Card.TFrame')
        text_card.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Text stats
        stats_frame = ttk.Frame(text_card)
        stats_frame.pack(fill='x', pady=5, padx=5)
        
        self.stats_label = ttk.Label(stats_frame,
                                    text="Characters: 0  |  Words: 0  |  Line: 1  |  Font: 11pt",
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
        text_container = tk.Frame(text_card)
        text_container.pack(fill='both', expand=True, padx=5, pady=(0, 5))
        
        self.text_input = tk.Text(text_container,
                                  wrap=tk.WORD,
                                  font=('Segoe UI', self.font_size),
                                  relief='flat',
                                  bg=self.colors['input_bg'],
                                  fg=self.colors['input_fg'],
                                  padx=10,
                                  pady=10,
                                  undo=True,
                                  maxundo=100)
        
        # Configure text tags
        self.text_input.tag_config("current_line", background=self.colors['current_line'])
        self.text_input.tag_config("marked", background=self.colors['marked'])
        
        # Create styled scrollbars
        self.text_scroll_y = ttk.Scrollbar(text_container, 
                                          orient='vertical', 
                                          command=self.text_input.yview,
                                          style="Vertical.TScrollbar")
        self.text_scroll_x = ttk.Scrollbar(text_container, 
                                          orient='horizontal', 
                                          command=self.text_input.xview,
                                          style="Horizontal.TScrollbar")
        
        self.text_input.configure(yscrollcommand=self.on_vertical_scroll, 
                                 xscrollcommand=self.on_horizontal_scroll)
        
        # Grid layout - initially hidden
        self.text_input.grid(row=0, column=0, sticky='nsew')
        self.text_scroll_y.grid(row=0, column=1, sticky='ns')
        self.text_scroll_x.grid(row=1, column=0, sticky='ew')
        
        # Initially hide scrollbars
        self.text_scroll_y.grid_remove()
        self.text_scroll_x.grid_remove()
        self.scrollbars_visible = False
        
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.text_input.bind('<KeyRelease>', self.on_text_change)
        self.text_input.bind('<ButtonRelease-1>', self.update_line_info)
        self.text_input.bind('<Configure>', lambda e: self.check_scrollbar_visibility())
        
        # Add sample text
        self.text_input.insert("1.0", """🎤 PIPER TTS - Enhanced Version

✨ FEATURES:
• Offline Text-to-Speech
• Dark/Light Mode Toggle
• Export Audio (WAV only)
• Speed Control (0.5x to 2.0x)
• Position Marking
• All Keyboard Shortcuts
• Font Size Control (Ctrl++/Ctrl+-)
• Auto-hiding Scrollbars

HOW TO USE:
1. Type or paste your text below
2. Select voice from dropdown
3. Adjust speed if needed
4. Click "▶ Speak" or use keyboard shortcuts
5. Use "📍 Mark" and "▶ From Mark" to read from specific positions
6. Click "💾 Export" to save as WAV file

KEYBOARD SHORTCUTS:
• Ctrl+Enter: Speak from beginning
• Ctrl+Shift+Enter: Speak from marked position
• Space: Pause/Resume
• Escape: Stop playback
• Ctrl+M: Mark position
• Ctrl+J: Jump to mark
• Ctrl+T: Toggle theme
• Ctrl+E: Export audio
• Ctrl+A: Select all text
• Ctrl+Z/Y: Undo/Redo
• Ctrl++/Ctrl+-: Increase/Decrease font size
• Ctrl+0: Reset font size

Try it now! Type your text below and click "▶ Speak".""")
        
        self.update_stats()
    
    def on_vertical_scroll(self, *args):
        """Handle vertical scrolling and show/hide scrollbar"""
        self.text_scroll_y.set(*args)
        self.check_scrollbar_visibility()
    
    def on_horizontal_scroll(self, *args):
        """Handle horizontal scrolling and show/hide scrollbar"""
        self.text_scroll_x.set(*args)
        self.check_scrollbar_visibility()
    
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
        self.root.bind('<Control-t>', lambda e: self.toggle_theme())
        self.root.bind('<Control-T>', lambda e: self.toggle_theme())
        self.root.bind('<Control-e>', lambda e: self.export_audio())
        self.root.bind('<Control-E>', lambda e: self.export_audio())
        
        # Font size shortcuts
        self.root.bind('<Control-plus>', lambda e: self.change_font_size(1))
        self.root.bind('<Control-equal>', lambda e: self.change_font_size(1))
        self.root.bind('<Control-minus>', lambda e: self.change_font_size(-1))
        self.root.bind('<Control-0>', lambda e: self.reset_font_size())
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts = """
        🔊 PLAYBACK CONTROLS:
        Ctrl+Enter      - Speak from beginning
        Ctrl+Shift+Enter - Speak from marked position
        Space           - Pause/Resume (when playing)
        Escape          - Stop playback
        Ctrl+E          - Export audio (WAV only)
        
        📍 POSITION NAVIGATION:
        Ctrl+M  - Mark current position
        Ctrl+J  - Jump to marked position
        
        🎨 THEME & DISPLAY:
        Ctrl+T  - Toggle Dark/Light mode
        Ctrl++  - Increase font size
        Ctrl+-  - Decrease font size
        Ctrl+0  - Reset font size
        
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
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Keyboard Shortcuts")
        dialog.geometry("600x450")
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, font=('Segoe UI', 10), 
                            padx=15, pady=15, relief='flat', bg='white')
        text_widget.insert("1.0", shortcuts)
        text_widget.config(state='disabled')
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        close_btn = ttk.Button(dialog, text="Close", command=dialog.destroy)
        close_btn.pack(pady=10)
        
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_text_change(self, event=None):
        self.update_stats()
        self.check_scrollbar_visibility()
    
    def update_stats(self):
        """Update character, word, line, and font size counts"""
        text = self.text_input.get("1.0", tk.END).strip()
        
        char_count = len(text)
        words = len(text.split()) if text else 0
        
        try:
            cursor_pos = self.text_input.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
        except:
            line_num = 1
        
        self.stats_label.config(text=f"Characters: {char_count:,}  |  Words: {words:,}  |  Line: {line_num}  |  Font: {self.font_size}pt")
    
    def update_line_info(self, event=None):
        """Update current line highlighting"""
        try:
            self.text_input.tag_remove("current_line", "1.0", tk.END)
            
            cursor_pos = self.text_input.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
            
            self.text_input.tag_add("current_line", f"{line_num}.0", f"{line_num}.end+1c")
            
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
        return None
    
    def speak(self, from_marked_position=False):
        """Start speaking text"""
        if self.is_playing:
            self.stop_speech()
            time.sleep(0.2)
        
        voice_key = self.get_selected_voice_key()
        if not voice_key:
            messagebox.showerror("No Voice", "Please select a voice first.")
            return
        
        if voice_key not in self.voice_files:
            messagebox.showerror("Voice Error", 
                               f"Voice '{voice_key}' not found.\n"
                               f"Please ensure voice files exist in:\n"
                               f"~/.local/share/piper-tts/voices/")
            return
        
        voice_info = self.voice_files[voice_key]
        
        if not os.path.exists(voice_info["onnx"]):
            messagebox.showerror("File Missing", 
                               f"Voice file not found:\n{voice_info['onnx']}")
            return
        
        full_text = self.text_input.get("1.0", tk.END).strip()
        
        text_to_speak = full_text
        start_position_info = "Speaking..."
        
        if from_marked_position and self.mark_position:
            text_to_speak = self.text_input.get(self.mark_position, tk.END).strip()
            if not text_to_speak:
                messagebox.showinfo("No text", "No text to speak from marked position.")
                return
            start_position_info = "Speaking from mark..."
            
            line, col = map(int, self.mark_position.split('.'))
            self.status_var.set(f"From line {line}")
        else:
            if not text_to_speak:
                messagebox.showwarning("No text", "Please enter some text to speak.")
                return
        
        self.status_var.set(start_position_info)
        self.speak_button.config(state='disabled')
        self.speak_from_mark_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        self.is_playing = True
        self.is_paused = False
        
        self.text_input.tag_remove("marked", "1.0", tk.END)
        if from_marked_position and self.mark_position:
            self.text_input.tag_add("marked", self.mark_position)
        
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
            
            cmd = ['piper', '--model', voice_info["onnx"], '--output-raw']
            
            if speed != 1.0:
                cmd.extend(['--length_scale', str(1.0/speed)])
            
            self.piper_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.aplay_process = subprocess.Popen(
                ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-c', '1'],
                stdin=self.piper_process.stdout,
                stderr=subprocess.PIPE
            )
            
            self.piper_process.stdin.write(text.encode())
            self.piper_process.stdin.close()
            
            while True:
                if not self.is_playing:
                    break
                
                if self.is_paused:
                    if self.aplay_process:
                        self.aplay_process.send_signal(signal.SIGSTOP)
                    while self.is_paused and self.is_playing:
                        time.sleep(0.1)
                    if self.aplay_process and self.aplay_process.poll() is None:
                        self.aplay_process.send_signal(signal.SIGCONT)
                
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
    
    def export_audio(self):
        """Export text as audio file (WAV only)"""
        voice_key = self.get_selected_voice_key()
        if not voice_key:
            messagebox.showerror("No Voice", "Please select a voice first.")
            return
        
        if voice_key not in self.voice_files:
            messagebox.showerror("Voice Error", f"Voice '{voice_key}' not found.")
            return
        
        voice_info = self.voice_files[voice_key]
        
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No text", "Please enter some text to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[
                ("WAV files", "*.wav"),
                ("All files", "*.*")
            ],
            title="Export Audio as WAV"
        )
        
        if not file_path:
            return
        
        if not file_path.lower().endswith('.wav'):
            file_path += '.wav'
        
        self.status_var.set("Exporting audio...")
        
        thread = threading.Thread(
            target=self.run_export,
            args=(text, voice_info, file_path),
            daemon=True
        )
        thread.start()
    
    def run_export(self, text, voice_info, file_path):
        """Export audio to WAV file - FIXED VERSION"""
        try:
            speed = self.speed_var.get()
            
            # Build command
            cmd = ['piper', '--model', voice_info["onnx"], '--output_file', file_path]
            
            if speed != 1.0:
                cmd.extend(['--length_scale', str(1.0/speed)])
            
            # Run piper with text input
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # Use text mode for easier string handling
            )
            
            # Send text and close stdin
            process.stdin.write(text)
            process.stdin.close()
            
            # Wait for process to complete
            stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
            
            # ALWAYS check if file was created successfully, regardless of return code
            if os.path.exists(file_path) and os.path.getsize(file_path) > 100:  # Minimum 100 bytes
                self.root.after(0, lambda: [
                    messagebox.showinfo("Success", f"Audio exported successfully!\n\n{file_path}"),
                    self.status_var.set("Export complete")
                ])
            else:
                # File wasn't created or is too small
                error_msg = stderr if stderr else "Unknown error"
                self.root.after(0, lambda: [
                    messagebox.showerror("Export Failed", f"Failed to create audio file:\n\n{error_msg[:200]}"),
                    self.status_var.set("Export failed")
                ])
                
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: [
                messagebox.showerror("Export Failed", "Export timed out after 5 minutes"),
                self.status_var.set("Export timed out")
            ])
        except Exception as e:
            self.root.after(0, lambda: [
                messagebox.showerror("Export Failed", f"Failed to export audio:\n\n{str(e)}"),
                self.status_var.set("Export failed")
            ])
    
    def pause_speech(self):
        """Pause or resume speech"""
        if not self.is_playing:
            return
        
        if not self.is_paused:
            self.is_paused = True
            self.pause_button.config(text="▶ Resume")
            self.status_var.set("Paused")
        else:
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
        
        self.text_input.tag_remove("marked", "1.0", tk.END)
        
        if not self.is_playing:
            self.status_var.set("Ready")
    
    def mark_position_func(self):
        """Mark current cursor position"""
        try:
            self.mark_position = self.text_input.index(tk.INSERT)
            self.speak_from_mark_button.config(state='normal')
            self.jump_mark_button.config(state='normal')
            
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
            self.check_scrollbar_visibility()
            self.mark_position = None
            self.speak_from_mark_button.config(state='disabled')
            self.jump_mark_button.config(state='disabled')
            self.status_var.set("Text cleared")
    
    def select_all_text(self, event=None):
        self.text_input.tag_add('sel', '1.0', 'end')
        self.text_input.focus()
        return "break"
    
    def undo_text(self, event=None):
        try:
            self.text_input.edit_undo()
            self.check_scrollbar_visibility()
        except:
            pass
        return "break"
    
    def redo_text(self, event=None):
        try:
            self.text_input.edit_redo()
            self.check_scrollbar_visibility()
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
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
