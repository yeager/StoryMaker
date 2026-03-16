"""Profile creation and editing view."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw

from storymaker.models.child_profile import ChildProfile


AVATAR_EMOJIS = ["🧒", "👦", "👧", "🧒🏻", "👦🏽", "👧🏿", "🦸", "🧙", "🧚", "🐱", "🐶", "🦊"]

INTEREST_OPTIONS = [
    ("🌲", "Natur"),
    ("🚀", "Rymden"),
    ("🐾", "Djur"),
    ("🏰", "Sagor"),
    ("🎨", "Konst"),
    ("⚽", "Sport"),
    ("🎵", "Musik"),
    ("🔬", "Vetenskap"),
    ("🍳", "Matlagning"),
    ("🏴‍☠️", "Pirater"),
    ("🐉", "Drakar"),
    ("🤖", "Robotar"),
]


class ProfileView(Gtk.Box):
    """Profile creation/editing form."""

    def __init__(self, window, profile=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self.profile = profile or ChildProfile()
        self.selected_interests = set(self.profile.interests)
        self.selected_avatar = self.profile.avatar_emoji

        self._build_ui()

    def _build_ui(self):
        """Build the profile form."""
        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label=_("Save"))
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)

        if self.profile.id:
            delete_btn = Gtk.Button(icon_name="user-trash-symbolic")
            delete_btn.add_css_class("destructive-action")
            delete_btn.connect("clicked", self._on_delete)
            header.pack_end(delete_btn)

        self.append(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(32)
        content.set_margin_end(32)

        # Avatar selection
        avatar_label = Gtk.Label(label=_("Select din avatar"))
        avatar_label.add_css_class("title-4")
        avatar_label.set_xalign(0)
        content.append(avatar_label)

        avatar_flow = Gtk.FlowBox()
        avatar_flow.set_max_children_per_line(6)
        avatar_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        avatar_flow.set_row_spacing(8)
        avatar_flow.set_column_spacing(8)

        self.avatar_buttons = {}
        for emoji in AVATAR_EMOJIS:
            btn = Gtk.ToggleButton()
            btn.set_child(Gtk.Label(label=emoji))
            btn.get_child().set_markup(f'<span size="x-large">{emoji}</span>')
            if emoji == self.selected_avatar:
                btn.set_active(True)
            btn.connect("toggled", self._on_avatar_toggled, emoji)
            self.avatar_buttons[emoji] = btn
            avatar_flow.append(btn)

        content.append(avatar_flow)

        # Name entry
        name_group = Adw.PreferencesGroup(title=_("About dig"))
        self.name_row = Adw.EntryRow(title=_("Name"))
        self.name_row.set_text(self.profile.name)
        name_group.add(self.name_row)

        # Age spinner
        self.age_row = Adw.SpinRow.new_with_range(6, 12, 1)
        self.age_row.set_title(_("Age"))
        self.age_row.set_value(self.profile.age)
        name_group.add(self.age_row)

        # Language selection
        self.lang_row = Adw.ComboRow(title=_("Language"))
        lang_model = Gtk.StringList.new(["Svenska", "English"])
        self.lang_row.set_model(lang_model)
        self.lang_row.set_selected(0 if self.profile.language == "sv" else 1)
        name_group.add(self.lang_row)

        content.append(name_group)

        # Interests
        interests_label = Gtk.Label(label=_("Vad tycker du om?"))
        interests_label.add_css_class("title-4")
        interests_label.set_xalign(0)
        interests_label.set_margin_top(8)
        content.append(interests_label)

        interests_flow = Gtk.FlowBox()
        interests_flow.set_max_children_per_line(4)
        interests_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        interests_flow.set_row_spacing(8)
        interests_flow.set_column_spacing(8)

        self.interest_buttons = {}
        for emoji, name in INTEREST_OPTIONS:
            btn = Gtk.ToggleButton(label=f"{emoji} {name}")
            btn.add_css_class("pill")
            if name in self.selected_interests:
                btn.set_active(True)
            btn.connect("toggled", self._on_interest_toggled, name)
            self.interest_buttons[name] = btn
            interests_flow.append(btn)

        content.append(interests_flow)

        scroll.set_child(content)
        self.append(scroll)

    def _on_avatar_toggled(self, button, emoji):
        """Handle avatar selection."""
        if button.get_active():
            self.selected_avatar = emoji
            # Deactivate other avatar buttons
            for e, btn in self.avatar_buttons.items():
                if e != emoji:
                    btn.set_active(False)

    def _on_interest_toggled(self, button, interest):
        """Handle interest selection."""
        if button.get_active():
            self.selected_interests.add(interest)
        else:
            self.selected_interests.discard(interest)

    def _on_save(self, button):
        """Save the profile."""
        name = self.name_row.get_text().strip()
        if not name:
            self.name_row.add_css_class("error")
            return

        self.profile.name = name
        self.profile.age = int(self.age_row.get_value())
        self.profile.language = "sv" if self.lang_row.get_selected() == 0 else "en"
        self.profile.avatar_emoji = self.selected_avatar
        self.profile.interests = list(self.selected_interests)

        self.window.db.save_profile(self.profile)

        # Ensure progress entry exists
        self.window.db.get_progress(self.profile.id)

        self.window.go_back()
        # Refresh welcome view
        self.window.welcome_view.refresh_profiles()

    def _on_delete(self, button):
        """Delete the profile after confirmation."""
        dialog = Adw.AlertDialog(
            heading=_("Delete profil?"),
            body=_("All stories and progress for {name} will be deleted.").format(
                name=self.profile.name
            ),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("delete", _("Delete"))
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_response)
        dialog.present(self.window)

    def _on_delete_response(self, dialog, response):
        if response == "delete":
            self.window.db.delete_profile(self.profile.id)
            self.window.go_back()
            self.window.welcome_view.refresh_profiles()
