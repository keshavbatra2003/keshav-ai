"""
Voice Service providing Text-to-Speech (TTS) audio playback and speech input support.
Uses native OS speech engines (macOS `say`, Windows SpeechSynthesizer, Linux `spd-say`)
with zero external runtime dependencies.
"""

import asyncio
import os
import platform
import re
import subprocess
from typing import Optional


class VoiceService:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.active_process: Optional[subprocess.Popen] = None
        self.is_speaking = False

    def clean_text_for_speech(self, text: str) -> str:
        """Strips markdown syntax, code blocks, URLs, and symbols for natural narration."""
        # Remove fenced code blocks
        text = re.sub(r"```[\s\S]*?```", " [Code snippet omitted for speech] ", text)
        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove markdown links [title](url) -> title
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Remove headers, asterisks, hash marks, blockquotes
        text = re.sub(r"[#*_\>~]", "", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def stop(self):
        """Immediately halts any active speech narration."""
        if self.active_process:
            try:
                self.active_process.terminate()
                self.active_process.kill()
            except Exception:
                pass
            self.active_process = None
        self.is_speaking = False

    async def speak_async(self, text: str):
        """Asynchronously narrates text using the native OS speech synthesizer."""
        self.stop()
        speech_text = self.clean_text_for_speech(text)
        if not speech_text:
            return

        self.is_speaking = True

        def _run_native_speech():
            try:
                if self.os_type == "darwin":  # macOS
                    self.active_process = subprocess.Popen(
                        ["say", "-v", "Samantha", speech_text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self.active_process.wait()

                elif self.os_type == "windows":  # Windows
                    escaped_text = speech_text.replace("'", "''")
                    ps_cmd = (
                        f"Add-Type -AssemblyName System.Speech; "
                        f"$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        f"$speak.Speak('{escaped_text}')"
                    )
                    self.active_process = subprocess.Popen(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self.active_process.wait()

                else:  # Linux (spd-say or espeak)
                    cmd = ["spd-say", speech_text] if self._has_cmd("spd-say") else ["espeak", speech_text]
                    self.active_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self.active_process.wait()
            except Exception as err:
                print("Speech playback error:", err)
            finally:
                self.is_speaking = False
                self.active_process = None

        await asyncio.to_thread(_run_native_speech)

    def _has_cmd(self, cmd_name: str) -> bool:
        import shutil
        return shutil.which(cmd_name) is not None


# Global singleton voice service
voice_service = VoiceService()
