"""Settings view for API keys and preferences."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw

from storymaker.config import CONFIG_DIR


class SettingsView(Gtk.Box):
    """Settings panel for API configuration and preferences."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self._config = self._load_config()

        self._build_ui()

    def _build_ui(self):
        header = Adw.HeaderBar()
        self.append(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(32)
        content.set_margin_end(32)

        # AI Provider settings
        ai_group = Adw.PreferencesGroup(
            title=_("AI-inställningar"),
            description=_("Välj AI-tjänst och ange API-nyckel. Utan nyckel används demo-läge."),
        )

        # Provider selection
        self.provider_row = Adw.ComboRow(title=_("AI-tjänst"))
        provider_model = Gtk.StringList.new(["Demo (ingen nyckel)", "OpenAI", "Anthropic"])
        self.provider_row.set_model(provider_model)
        provider_idx = {"demo": 0, "openai": 1, "anthropic": 2}
        self.provider_row.set_selected(provider_idx.get(self._config.get("provider", "demo"), 0))
        ai_group.add(self.provider_row)

        # API Key
        self.api_key_row = Adw.PasswordEntryRow(title=_("API-nyckel"))
        self.api_key_row.set_text(self._config.get("api_key", ""))
        ai_group.add(self.api_key_row)

        content.append(ai_group)

        # TTS settings
        tts_group = Adw.PreferencesGroup(title=_("Uppläsning (TTS)"))

        tts_status = _("Tillgänglig") if self.window.tts.is_available else _("Ej tillgänglig")
        tts_row = Adw.ActionRow(
            title=_("Text-till-tal"),
            subtitle=f"{tts_status} ({self.window.tts.backend_name})",
        )
        tts_group.add(tts_row)

        if not self.window.tts.is_available:
            hint_row = Adw.ActionRow(
                title=_("Installera espeak-ng för uppläsning"),
                subtitle="sudo apt install espeak-ng",
            )
            tts_group.add(hint_row)

        content.append(tts_group)

        # About section
        about_group = Adw.PreferencesGroup(title=_("Om StoryMaker"))
        about_row = Adw.ActionRow(
            title="StoryMaker 1.0.0",
            subtitle=_("Interaktiva berättelser med AI och piktogram"),
        )
        about_group.add(about_row)
        content.append(about_group)

        # Save button
        save_btn = Gtk.Button(label=_("Spara inställningar"))
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_halign(Gtk.Align.CENTER)
        save_btn.set_margin_top(16)
        save_btn.connect("clicked", self._on_save)
        content.append(save_btn)

        scroll.set_child(content)
        self.append(scroll)

    def _on_save(self, button):
        """Save settings."""
        providers = ["demo", "openai", "anthropic"]
        provider = providers[self.provider_row.get_selected()]
        api_key = self.api_key_row.get_text().strip()

        self._config["provider"] = provider
        self._config["api_key"] = api_key
        self._save_config()

        # Update engine
        self.window.engine.set_provider(provider, api_key)

        # Show confirmation
        toast = Adw.Toast(title=_("Inställningar sparade!"))
        toast.set_timeout(2)
        # Find the toast overlay or just go back
        self.window.go_back()

    def _load_config(self) -> dict:
        """Load config from file."""
        import json
        config_file = CONFIG_DIR / "settings.json"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"provider": "demo", "api_key": ""}

    def _save_config(self):
        """Save config to file."""
        import json
        config_file = CONFIG_DIR / "settings.json"
        config_file.write_text(json.dumps(self._config, indent=2))
        # Restrict permissions
        config_file.chmod(0o600)
