"""Text-to-Speech service using espeak-ng or system TTS."""

import shutil
import subprocess
import threading
from typing import Optional


class TTSService:
    """Text-to-Speech service for reading stories aloud."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._backend = self._detect_backend()

    def _detect_backend(self) -> Optional[str]:
        """Detect available TTS backend."""
        if shutil.which("espeak-ng"):
            return "espeak-ng"
        if shutil.which("espeak"):
            return "espeak"
        # macOS
        if shutil.which("say"):
            return "say"
        return None

    @property
    def is_available(self) -> bool:
        return self._backend is not None

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def speak(self, text: str, language: str = "sv"):
        """Speak the given text. Non-blocking."""
        self.stop()

        if not self._backend:
            return

        def _run():
            with self._lock:
                try:
                    if self._backend in ("espeak-ng", "espeak"):
                        lang_code = "sv" if language == "sv" else "en"
                        self._process = subprocess.Popen(
                            [self._backend, "-v", lang_code, "-s", "140", "-p", "60", text],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    elif self._backend == "say":
                        voice = "Alva" if language == "sv" else "Samantha"
                        self._process = subprocess.Popen(
                            ["say", "-v", voice, "-r", "140", text],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    if self._process:
                        self._process.wait()
                except OSError:
                    pass
                finally:
                    self._process = None

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def stop(self):
        """Stop any ongoing speech."""
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                self._process = None

    @property
    def backend_name(self) -> str:
        return self._backend or "none"
