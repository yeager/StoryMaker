"""Application configuration and constants."""

import os
from pathlib import Path

APP_ID = "org.github.storymaker"
APP_NAME = "StoryMaker"
APP_VERSION = "1.0.0"

# XDG directories
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "storymaker"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "storymaker"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "storymaker"

# Ensure directories exist
for d in (DATA_DIR, CACHE_DIR, CONFIG_DIR, CACHE_DIR / "pictograms"):
    d.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DATA_DIR / "storymaker.db"

# ARASAAC API
ARASAAC_API_BASE = "https://api.arasaac.org/v1"
PICTOGRAM_CACHE_DIR = CACHE_DIR / "pictograms"

# Age bands for content adaptation
AGE_BANDS = {
    "young": (6, 8),
    "middle": (9, 10),
    "older": (11, 12),
}

# Default story settings
DEFAULT_CHOICES_COUNT = 3
MAX_STORY_LENGTH = 20  # max chapters

# CSS for child-friendly fonts
CHILD_FONT_SIZE = "18px"
CHILD_FONT_FAMILY = "sans-serif"
