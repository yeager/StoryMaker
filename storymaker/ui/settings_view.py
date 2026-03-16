"""Settings view for API keys, TTS voice selection, and preferences."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw

from storymaker.config import CONFIG_DIR
from storymaker.utils.i18n import _


class SettingsView(Gtk.Box):
    """Settings panel for all StoryMaker preferences."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self._config = self._load_config()
        self._build_ui()

    def _build_ui(self):
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=_("Settings")))
        back_btn = Gtk.Button(icon_name="go-previous-symbolic")
        back_btn.connect("clicked", lambda _: self.window.go_back())
        header.pack_start(back_btn)
        self.append(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # === TTS SETTINGS ===
        tts_group = Adw.PreferencesGroup(
            title=_("Voice and Reading"),
            description=_("Settings for text-to-speech reading"),
        )

        # Voice language
        self.voice_lang_row = Adw.ComboRow(title=_("Story language"))
        lang_model = Gtk.StringList.new([_("Swedish"), _("English")])
        self.voice_lang_row.set_model(lang_model)
        self.voice_lang_row.set_selected(0 if self._config.get("voice_language", "sv") == "sv" else 1)
        tts_group.add(self.voice_lang_row)

        # Voice gender (for English)
        self.voice_gender_row = Adw.ComboRow(title=_("English voice"))
        gender_model = Gtk.StringList.new([_("Female (Lessac)"), _("Male (Ryan)")])
        self.voice_gender_row.set_model(gender_model)
        self.voice_gender_row.set_selected(0 if self._config.get("voice_gender", "female") == "female" else 1)
        tts_group.add(self.voice_gender_row)

        # TTS status
        tts_status = _("Piper TTS available") if self.window.tts.is_available else _("Piper TTS not found")
        backend = self.window.tts.backend_name
        tts_info_row = Adw.ActionRow(
            title=_("TTS Engine"),
            subtitle=f"{tts_status} ({backend})",
        )
        tts_group.add(tts_info_row)

        # Auto-read toggle
        self.auto_read_row = Adw.SwitchRow(
            title=_("Read aloud automatically"),
            subtitle=_("Read each chapter aloud when it appears"),
        )
        self.auto_read_row.set_active(self._config.get("auto_read", False))
        tts_group.add(self.auto_read_row)

        content.append(tts_group)

        # === AI SETTINGS ===
        ai_group = Adw.PreferencesGroup(
            title=_("AI Story Generation"),
            description=_("Without API key, pre-made stories and demo mode are used."),
        )

        self.provider_row = Adw.ComboRow(title=_("AI service"))
        provider_model = Gtk.StringList.new([_("Demo (no key needed)"), "OpenAI", "Anthropic"])
        self.provider_row.set_model(provider_model)
        provider_idx = {"demo": 0, "openai": 1, "anthropic": 2}
        self.provider_row.set_selected(provider_idx.get(self._config.get("provider", "demo"), 0))
        ai_group.add(self.provider_row)

        self.api_key_row = Adw.PasswordEntryRow(title=_("API key"))
        self.api_key_row.set_text(self._config.get("api_key", ""))
        ai_group.add(self.api_key_row)

        content.append(ai_group)

        # === DISPLAY SETTINGS ===
        display_group = Adw.PreferencesGroup(
            title=_("Display"),
        )

        self.font_size_row = Adw.ComboRow(title=_("Text size"))
        size_model = Gtk.StringList.new([_("Normal"), _("Large"), _("Extra large")])
        self.font_size_row.set_model(size_model)
        sizes = {"normal": 0, "large": 1, "xlarge": 2}
        self.font_size_row.set_selected(sizes.get(self._config.get("font_size", "normal"), 0))
        display_group.add(self.font_size_row)

        self.show_pictograms_row = Adw.SwitchRow(
            title=_("Show pictograms"),
            subtitle=_("Display ARASAAC pictograms alongside story text"),
        )
        self.show_pictograms_row.set_active(self._config.get("show_pictograms", True))
        display_group.add(self.show_pictograms_row)

        content.append(display_group)

        # === ABOUT ===
        about_group = Adw.PreferencesGroup(title=_("About"))
        about_row = Adw.ActionRow(
            title="StoryMaker 1.0.0",
            subtitle=_("Interactive stories for children with AI and Piper TTS"),
        )
        about_group.add(about_row)
        content.append(about_group)

        # Save button
        save_btn = Gtk.Button(label=_("Save"))
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_halign(Gtk.Align.CENTER)
        save_btn.set_margin_top(16)
        save_btn.connect("clicked", self._on_save)
        content.append(save_btn)

        scroll.set_child(content)
        self.append(scroll)

    def _on_save(self, button):
        providers = ["demo", "openai", "anthropic"]
        languages = ["sv", "en"]
        genders = ["female", "male"]
        font_sizes = ["normal", "large", "xlarge"]

        self._config["provider"] = providers[self.provider_row.get_selected()]
        self._config["api_key"] = self.api_key_row.get_text().strip()
        self._config["voice_language"] = languages[self.voice_lang_row.get_selected()]
        self._config["voice_gender"] = genders[self.voice_gender_row.get_selected()]
        self._config["auto_read"] = self.auto_read_row.get_active()
        self._config["font_size"] = font_sizes[self.font_size_row.get_selected()]
        self._config["show_pictograms"] = self.show_pictograms_row.get_active()
        self._save_config()

        self.window.engine.set_provider(self._config["provider"], self._config["api_key"])

        toast = Adw.Toast(title=_("Settings saved"))
        toast.set_timeout(2)
        self.window.go_back()

    def _load_config(self) -> dict:
        import json
        config_file = CONFIG_DIR / "settings.json"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"provider": "demo", "api_key": "", "voice_language": "sv",
                "voice_gender": "female", "auto_read": False, "font_size": "normal",
                "show_pictograms": True}

    def _save_config(self):
        import json
        config_file = CONFIG_DIR / "settings.json"
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(self._config, indent=2))
        config_file.chmod(0o600)

    def get_config(self) -> dict:
        return self._config
