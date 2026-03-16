"""Welcome view with profile selection."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from storymaker.utils.i18n import _


class WelcomeView(Gtk.Box):
    """Welcome screen with profile selection and creation."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window

        # Header bar with settings and library buttons
        header = Adw.HeaderBar()
        
        library_btn = Gtk.Button(icon_name="folder-symbolic")
        library_btn.set_tooltip_text(_("Story Library"))
        library_btn.connect("clicked", lambda _: self.window.show_library())
        header.pack_end(library_btn)
        
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text(_("Settings"))
        settings_btn.connect("clicked", lambda _: self.window.show_settings())
        header.pack_end(settings_btn)
        
        self.append(header)

        # Content area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(32)
        content.set_margin_bottom(32)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_vexpand(True)

        # Welcome title
        title = Gtk.Label(label="✨ StoryMaker ✨")
        title.add_css_class("welcome-title")
        content.append(title)

        subtitle = Gtk.Label(label=_("Create magical stories with AI!"))
        subtitle.add_css_class("welcome-subtitle")
        content.append(subtitle)

        # Profile list
        profiles_label = Gtk.Label(label=_("Who is reading today?"))
        profiles_label.add_css_class("title-3")
        profiles_label.set_margin_top(24)
        content.append(profiles_label)

        self.profiles_box = Gtk.FlowBox()
        self.profiles_box.set_homogeneous(True)
        self.profiles_box.set_max_children_per_line(4)
        self.profiles_box.set_min_children_per_line(2)
        self.profiles_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.profiles_box.set_row_spacing(12)
        self.profiles_box.set_column_spacing(12)
        self.profiles_box.set_margin_top(12)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.profiles_box)
        content.append(scrolled)

        # Add new profile button
        add_btn = Gtk.Button(label=_("➕ New reader"))
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("pill")
        add_btn.set_halign(Gtk.Align.CENTER)
        add_btn.connect("clicked", lambda _: self.window.show_profile_editor())
        content.append(add_btn)

        self.append(content)
        self.refresh_profiles()

    def refresh_profiles(self):
        """Reload and display all profiles."""
        # Clear existing
        while child := self.profiles_box.get_first_child():
            self.profiles_box.remove(child)

        profiles = self.window.db.get_profiles()
        for profile in profiles:
            card = self._create_profile_card(profile)
            self.profiles_box.append(card)

    def _create_profile_card(self, profile):
        """Create a clickable profile card."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_halign(Gtk.Align.CENTER)

        # Avatar emoji
        avatar = Gtk.Label(label=profile.avatar_emoji)
        avatar.set_markup(f'<span size="xx-large">{profile.avatar_emoji}</span>')
        box.append(avatar)

        # Name
        name = Gtk.Label(label=profile.name)
        name.add_css_class("title-4")
        box.append(name)

        # Age
        age = Gtk.Label(label=f"{profile.age} {_("year")}")
        age.add_css_class("dim-label")
        box.append(age)

        # Buttons row
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_halign(Gtk.Align.CENTER)

        play_btn = Gtk.Button(label=_("Spela"))
        play_btn.add_css_class("suggested-action")
        play_btn.connect("clicked", lambda _, p=profile: self.window.show_story_selector(p))
        btn_box.append(play_btn)

        progress_btn = Gtk.Button(icon_name="view-list-symbolic")
        progress_btn.set_tooltip_text(_("Progress"))
        progress_btn.connect("clicked", lambda _, p=profile: self.window.show_progress(p))
        btn_box.append(progress_btn)

        edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
        edit_btn.set_tooltip_text(_("Edit"))
        edit_btn.connect("clicked", lambda _, p=profile: self.window.show_profile_editor(p))
        btn_box.append(edit_btn)

        box.append(btn_box)

        # Wrap in a frame for card styling
        frame = Gtk.Frame()
        frame.add_css_class("profile-card")
        frame.set_child(box)
        return frame
