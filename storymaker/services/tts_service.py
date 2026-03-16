"""Text-to-Speech service using Piper TTS with Swedish Alma and English voices."""

import os
import shutil
import subprocess
import tempfile
import threading
from typing import Optional


class TTSService:
    """Text-to-Speech service for reading stories aloud.
    
    Uses Piper TTS with:
    - Swedish: Alma voice (sv_SE-alma-medium)
    - English female: en_US-lessac-medium
    - English male: en_US-ryan-medium
    """

    # Voice models
    VOICES = {
        "sv_female": "sv_SE-alma-medium",      # Alma
        "en_female": "en_US-lessac-medium",
        "en_male": "en_US-ryan-medium",
    }

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._piper_bin = self._find_piper()
        self._voice_dir = self._find_voice_dir()

    def _find_piper(self) -> Optional[str]:
        """Find Piper binary."""
        for path in [
            shutil.which("piper"),
            "/usr/bin/piper",
            "/usr/local/bin/piper",
            "/opt/homebrew/bin/piper",
        ]:
            if path and os.path.isfile(path):
                return path
        return None

    def _find_voice_dir(self) -> str:
        """Find directory with Piper voice models."""
        candidates = [
            "/usr/share/piper-voices",
            "/usr/local/share/piper-voices",
            os.path.expanduser("~/.local/share/piper-voices"),
            "/opt/homebrew/share/piper-voices",
        ]
        for d in candidates:
            if os.path.isdir(d):
                return d
        # Default — Piper can download models automatically
        return os.path.expanduser("~/.local/share/piper-voices")

    @property
    def is_available(self) -> bool:
        return self._piper_bin is not None

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    @property
    def backend_name(self) -> str:
        return "piper" if self._piper_bin else "none"

    def get_voice_model(self, language: str = "sv", gender: str = "female") -> str:
        """Get the Piper voice model name for language and gender."""
        if language == "sv":
            return self.VOICES["sv_female"]  # Alma
        elif gender == "male":
            return self.VOICES["en_male"]
        else:
            return self.VOICES["en_female"]

    def _resolve_model_path(self, model_name: str) -> str:
        """Resolve model name to full path, or return name for Piper to download."""
        # Check if .onnx file exists locally
        for ext in [".onnx", ""]:
            full_path = os.path.join(self._voice_dir, model_name + ext)
            if os.path.isfile(full_path):
                return full_path
        # Return just the name — Piper will download it
        return model_name

    def speak(self, text: str, language: str = "sv", gender: str = "female",
              on_done=None):
        """Speak the given text using Piper TTS. Non-blocking.
        
        Args:
            text: Text to speak.
            language: 'sv' for Swedish, 'en' for English.
            gender: 'female' or 'male' (English only, Swedish always Alma).
            on_done: Optional callback when speech finishes.
        """
        self.stop()

        if not self._piper_bin:
            if on_done:
                on_done()
            return

        model = self.get_voice_model(language, gender)
        model_path = self._resolve_model_path(model)

        def _run():
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                    wav_path = wav_file.name

                # Generate speech with Piper
                with self._lock:
                    self._process = subprocess.Popen(
                        [self._piper_bin, "--model", model_path,
                         "--output_file", wav_path],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._process.communicate(input=text.encode("utf-8"))

                # Play the WAV file
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 44:
                    player = self._find_player()
                    if player:
                        with self._lock:
                            self._process = subprocess.Popen(
                                player + [wav_path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            self._process.wait()

                # Cleanup
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

            except (OSError, subprocess.SubprocessError):
                pass
            finally:
                with self._lock:
                    self._process = None
                if on_done:
                    on_done()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _find_player(self) -> Optional[list]:
        """Find an audio player."""
        for cmd in [["aplay"], ["paplay"], ["pw-play"],
                    ["ffplay", "-nodisp", "-autoexit"]]:
            if shutil.which(cmd[0]):
                return cmd
        return None

    def stop(self):
        """Stop any ongoing speech."""
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                self._process = None
