"""ARASAAC pictogram API client with caching."""

import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional

from storymaker.config import ARASAAC_API_BASE, PICTOGRAM_CACHE_DIR


# Local keyword-to-emoji fallback for common Swedish words
EMOJI_FALLBACKS = {
    "skog": "🌲", "träd": "🌳", "sol": "☀️", "måne": "🌙", "stjärna": "⭐",
    "hund": "🐕", "katt": "🐱", "häst": "🐴", "fågel": "🐦", "fisk": "🐟",
    "räv": "🦊", "björn": "🐻", "uggla": "🦉", "kanin": "🐰", "mus": "🐭",
    "hus": "🏠", "slott": "🏰", "skola": "🏫", "sjukhus": "🏥", "butik": "🏪",
    "bok": "📖", "penna": "✏️", "boll": "⚽", "cykel": "🚲", "bil": "🚗",
    "vatten": "💧", "eld": "🔥", "berg": "⛰️", "hav": "🌊", "flod": "🏞️",
    "äventyr": "🗺️", "hjälte": "🦸", "prinsessa": "👸", "drake": "🐉",
    "nyckel": "🔑", "bro": "🌉", "troll": "🧌", "gåta": "❓", "svar": "💡",
    "regnbåge": "🌈", "djur": "🐾", "blommor": "🌸", "mat": "🍎",
    "vän": "🤝", "familj": "👨‍👩‍👧‍👦", "barn": "🧒", "glad": "😊",
    "ledsen": "😢", "rädd": "😨", "arg": "😠", "modig": "💪",
    "springa": "🏃", "simma": "🏊", "flyga": "✈️", "sjunga": "🎵",
    "dansa": "💃", "sova": "😴", "äta": "🍽️", "läsa": "📚",
}


class PictogramCache:
    """On-disk cache for pictogram metadata."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or PICTOGRAM_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.cache_dir / "metadata.json"
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        if self._metadata_file.exists():
            try:
                return json.loads(self._metadata_file.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_metadata(self):
        self._metadata_file.write_text(json.dumps(self._metadata, ensure_ascii=False))

    def get(self, keyword: str) -> Optional[dict]:
        return self._metadata.get(keyword)

    def put(self, keyword: str, data: dict):
        self._metadata[keyword] = data
        self._save_metadata()

    def get_image_path(self, pictogram_id: int) -> Optional[Path]:
        path = self.cache_dir / f"{pictogram_id}.png"
        if path.exists():
            return path
        return None


class ArasaacClient:
    """Client for the ARASAAC pictogram API."""

    def __init__(self):
        self.cache = PictogramCache()
        self.base_url = ARASAAC_API_BASE

    def search_pictogram(self, keyword: str, language: str = "sv") -> Optional[dict]:
        """Search for a pictogram by keyword. Returns metadata with id."""
        # Check cache first
        cached = self.cache.get(keyword)
        if cached:
            return cached

        # Map Swedish locale code
        locale = "se" if language == "sv" else language

        try:
            url = f"{self.base_url}/pictograms/{locale}/search/{urllib.parse.quote(keyword)}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read())
                if data and isinstance(data, list) and len(data) > 0:
                    result = {
                        "id": data[0]["_id"],
                        "keyword": keyword,
                        "keywords": data[0].get("keywords", []),
                    }
                    self.cache.put(keyword, result)
                    return result
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
            pass
        return None

    def download_pictogram(self, pictogram_id: int, size: int = 100) -> Optional[Path]:
        """Download a pictogram image. Returns path to cached file."""
        # Check cache
        cached_path = self.cache.get_image_path(pictogram_id)
        if cached_path:
            return cached_path

        try:
            url = f"{self.base_url}/pictograms/{pictogram_id}?download=true&resolution={size}"
            path = PICTOGRAM_CACHE_DIR / f"{pictogram_id}.png"
            urllib.request.urlretrieve(url, str(path))
            return path
        except (urllib.error.URLError, TimeoutError):
            return None

    def get_emoji_for_keyword(self, keyword: str) -> str:
        """Get an emoji representation for a keyword (fallback)."""
        return EMOJI_FALLBACKS.get(keyword.lower(), "")

    def get_pictogram_or_emoji(self, keyword: str, language: str = "sv") -> dict:
        """Try to get a pictogram, fall back to emoji."""
        result = self.search_pictogram(keyword, language)
        if result:
            image_path = self.download_pictogram(result["id"])
            if image_path:
                result["image_path"] = str(image_path)
                return result

        emoji = self.get_emoji_for_keyword(keyword)
        return {"keyword": keyword, "emoji": emoji, "image_path": None}
