#!/usr/bin/env python3
"""
Voice Manager for Piper TTS
Handles voice discovery, downloading, and management
"""

import os
import json
import shutil
import requests
from pathlib import Path
from tkinter import messagebox
import threading
from voice_database import VOICE_DATABASE, get_all_voices, get_voice_by_id

class VoiceManager:
    def __init__(self, voices_dir=None):
        if voices_dir is None:
            self.voices_dir = os.path.expanduser("~/.local/share/piper-tts/voices")
        else:
            self.voices_dir = voices_dir
        
        # Ensure voices directory exists
        os.makedirs(self.voices_dir, exist_ok=True)
    
    def scan_available_voices(self):
        """Scan voices directory for installed voices"""
        installed_voices = {}
        
        if not os.path.exists(self.voices_dir):
            return installed_voices
        
        for item in os.listdir(self.voices_dir):
            if item.endswith('.onnx'):
                voice_id = item[:-5]  # Remove .onnx extension
                onnx_path = os.path.join(self.voices_dir, item)
                json_path = os.path.join(self.voices_dir, f"{voice_id}.onnx.json")
                
                # Check if both files exist
                if os.path.exists(json_path):
                    # Get voice info from database or extract from JSON
                    voice_info = get_voice_by_id(voice_id)
                    
                    if voice_info:
                        # Voice is in our database
                        installed_voices[voice_id] = {
                            "name": voice_info["name"],
                            "language": voice_info["language"],
                            "gender": voice_info["gender"],
                            "quality": voice_info["quality"],
                            "size_mb": voice_info["size_mb"],
                            "description": voice_info["description"],
                            "installed": True,
                            "onnx_path": onnx_path,
                            "json_path": json_path
                        }
                    else:
                        # Voice not in database - extract from JSON
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            
                            # Try to extract info
                            name = config.get("dataset", {}).get("language", {}).get("name", voice_id)
                            language = config.get("dataset", {}).get("language", {}).get("code", "Unknown")
                            gender = config.get("dataset", {}).get("gender", "Unknown")
                            
                            installed_voices[voice_id] = {
                                "name": f"{voice_id} (Custom)",
                                "language": language,
                                "gender": gender,
                                "quality": "Unknown",
                                "size_mb": os.path.getsize(onnx_path) / (1024 * 1024),
                                "description": "Custom voice file",
                                "installed": True,
                                "onnx_path": onnx_path,
                                "json_path": json_path,
                                "is_custom": True
                            }
                        except:
                            # Minimal info if JSON parsing fails
                            installed_voices[voice_id] = {
                                "name": voice_id,
                                "language": "Unknown",
                                "gender": "Unknown",
                                "quality": "Unknown",
                                "size_mb": os.path.getsize(onnx_path) / (1024 * 1024),
                                "description": "Unknown voice file",
                                "installed": True,
                                "onnx_path": onnx_path,
                                "json_path": json_path,
                                "is_custom": True
                            }
        
        return installed_voices
    
    def get_all_available_voices(self):
        """Get all voices (installed + downloadable)"""
        installed = self.scan_available_voices()
        all_voices = {}
        
        # Add all database voices
        for lang_code, voices in VOICE_DATABASE.items():
            for voice_id, voice_info in voices.items():
                is_installed = voice_id in installed
                
                all_voices[voice_id] = {
                    "name": voice_info["name"],
                    "language": voice_info["language"],
                    "gender": voice_info["gender"],
                    "quality": voice_info["quality"],
                    "size_mb": voice_info["size_mb"],
                    "description": voice_info["description"],
                    "installed": is_installed,
                    "download_url": voice_info["download_url"],
                    "config_url": voice_info["config_url"]
                }
                
                # Add path info if installed
                if is_installed:
                    all_voices[voice_id]["onnx_path"] = installed[voice_id]["onnx_path"]
                    all_voices[voice_id]["json_path"] = installed[voice_id]["json_path"]
        
        # Add custom voices (not in database)
        for voice_id, voice_info in installed.items():
            if voice_id not in all_voices:
                all_voices[voice_id] = voice_info
        
        return all_voices
    
    def download_voice(self, voice_id, progress_callback=None, status_callback=None):
        """Download a voice from the database"""
        voice_info = get_voice_by_id(voice_id)
        if not voice_info:
            return False, f"Voice {voice_id} not found in database"
        
        # Create temp directory
        temp_dir = os.path.join(self.voices_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        onnx_path = os.path.join(self.voices_dir, f"{voice_id}.onnx")
        json_path = os.path.join(self.voices_dir, f"{voice_id}.onnx.json")
        
        try:
            # Download ONNX file
            if status_callback:
                status_callback(f"Downloading {voice_info['name']}...")
            
            onnx_url = voice_info["download_url"]
            response = requests.get(onnx_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            temp_onnx = os.path.join(temp_dir, f"{voice_id}.onnx")
            with open(temp_onnx, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            # Download JSON config
            if status_callback:
                status_callback("Downloading configuration...")
            
            json_url = voice_info["config_url"]
            response = requests.get(json_url)
            temp_json = os.path.join(temp_dir, f"{voice_id}.onnx.json")
            with open(temp_json, 'wb') as f:
                f.write(response.content)
            
            # Move files to final location
            shutil.move(temp_onnx, onnx_path)
            shutil.move(temp_json, json_path)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if status_callback:
                status_callback(f"Downloaded {voice_info['name']} successfully!")
            
            return True, "Download successful"
            
        except Exception as e:
            # Clean up on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False, f"Download failed: {str(e)}"
    
    def delete_voice(self, voice_id):
        """Delete installed voice"""
        onnx_path = os.path.join(self.voices_dir, f"{voice_id}.onnx")
        json_path = os.path.join(self.voices_dir, f"{voice_id}.onnx.json")
        
        try:
            if os.path.exists(onnx_path):
                os.remove(onnx_path)
            if os.path.exists(json_path):
                os.remove(json_path)
            return True, "Voice deleted"
        except Exception as e:
            return False, f"Failed to delete voice: {str(e)}"
    
    def get_voice_info(self, voice_id):
        """Get detailed info about a voice"""
        # First check if it's installed
        installed = self.scan_available_voices()
        if voice_id in installed:
            return installed[voice_id]
        
        # Check database
        voice_info = get_voice_by_id(voice_id)
        if voice_info:
            return {
                **voice_info,
                "installed": False
            }
        
        return None
    
    def get_voice_paths(self, voice_id):
        """Get paths for a voice (returns None if not installed)"""
        onnx_path = os.path.join(self.voices_dir, f"{voice_id}.onnx")
        json_path = os.path.join(self.voices_dir, f"{voice_id}.onnx.json")
        
        if os.path.exists(onnx_path) and os.path.exists(json_path):
            return {
                "onnx": onnx_path,
                "json": json_path
            }
        return None
