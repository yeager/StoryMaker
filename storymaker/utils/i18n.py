"""Internationalization setup using gettext."""

import gettext
import locale
import os
from pathlib import Path


DOMAIN = "storymaker"
_locale_dir = None


def get_locale_dir():
    """Find the locale directory."""
    global _locale_dir
    if _locale_dir:
        return _locale_dir

    # Check development path first
    dev_path = Path(__file__).parent.parent.parent / "po" / "locale"
    if dev_path.exists():
        _locale_dir = str(dev_path)
        return _locale_dir

    # Check system paths
    for path in [
        Path("/usr/share/locale"),
        Path("/usr/local/share/locale"),
        Path.home() / ".local" / "share" / "locale",
    ]:
        if path.exists():
            _locale_dir = str(path)
            return _locale_dir

    _locale_dir = str(dev_path)
    return _locale_dir


def setup_i18n():
    """Initialize gettext for the application."""
    locale_dir = get_locale_dir()

    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        pass

    gettext.bindtextdomain(DOMAIN, locale_dir)
    gettext.textdomain(DOMAIN)

    import builtins
    builtins._ = gettext.gettext
    builtins.ngettext = gettext.ngettext


def get_language():
    """Get the current language code."""
    lang = os.environ.get("LANGUAGE", os.environ.get("LANG", "sv_SE"))
    return lang.split("_")[0].split(".")[0]
