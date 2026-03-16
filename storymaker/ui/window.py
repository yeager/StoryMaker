"""Main application window."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

from storymaker.ui.welcome_view import WelcomeView
from storymaker.ui.story_view import StoryView
from storymaker.ui.quiz_view import QuizView
from storymaker.ui.profile_view import ProfileView
from storymaker.ui.progress_view import ProgressView
from storymaker.ui.settings_view import SettingsView
from storymaker.engine.story_engine import StoryEngine
from storymaker.services.tts_service import TTSService


class StoryMakerWindow(Adw.ApplicationWindow):
    """The main application window with navigation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("StoryMaker")
        self.set_default_size(900, 700)

        app = self.get_application()
        self.db = app.db
        self.engine = StoryEngine()
        self.tts = TTSService()
        self.current_profile = None

        self._build_ui()

    def _build_ui(self):
        """Build the main UI layout."""
        # Main navigation view
        self.nav_view = Adw.NavigationView()
        self.set_content(self.nav_view)

        # Welcome page (initial)
        self.welcome_view = WelcomeView(self)
        welcome_page = Adw.NavigationPage(
            title="StoryMaker",
            child=self.welcome_view,
        )
        self.nav_view.push(welcome_page)

    def show_profile_editor(self, profile=None):
        """Navigate to profile editor."""
        view = ProfileView(self, profile)
        page = Adw.NavigationPage(title=_("Profil"), child=view)
        self.nav_view.push(page)

    def show_story_selector(self, profile):
        """Show story theme selector for a profile."""
        self.current_profile = profile
        view = StoryThemeSelector(self)
        page = Adw.NavigationPage(title=_("Select adventure"), child=view)
        self.nav_view.push(page)

    def show_story(self, profile, theme):
        """Start and show a story."""
        self.current_profile = profile
        view = StoryView(self, profile, theme)
        page = Adw.NavigationPage(title=theme, child=view)
        self.nav_view.push(page)

    def show_quiz(self, story):
        """Show quiz for a story."""
        view = QuizView(self, story)
        page = Adw.NavigationPage(title=_("Reading comprehension"), child=view)
        self.nav_view.push(page)

    def show_progress(self, profile):
        """Show progress dashboard."""
        view = ProgressView(self, profile)
        page = Adw.NavigationPage(title=_("Framsteg"), child=view)
        self.nav_view.push(page)

    def show_settings(self):
        """Show settings."""
        view = SettingsView(self)
        page = Adw.NavigationPage(title=_("Settings"), child=view)
        self.nav_view.push(page)

    def go_back(self):
        """Navigate back."""
        self.nav_view.pop()

    def go_home(self):
        """Navigate to home/welcome."""
        while self.nav_view.get_navigation_stack().get_n_items() > 1:
            self.nav_view.pop()
        self.welcome_view.refresh_profiles()


class StoryThemeSelector(Gtk.Box):
    """Theme selector for starting a new story."""

    THEMES = [
        ("🌲 Den Förtrollade Skogen", "Den Förtrollade Skogen"),
        ("🚀 Rymdäventyret", "Rymdäventyret"),
        ("🏰 Det Hemliga Slottet", "Det Hemliga Slottet"),
        ("🌊 Havets Mysterium", "Havets Mysterium"),
        ("🐉 Drakens Gåta", "Drakens Gåta"),
        ("🎪 Den Magiska Cirkusen", "Den Magiska Cirkusen"),
    ]

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window = window
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        title = Gtk.Label(label=_("Select a theme for your story!"))
        title.add_css_class("title-2")
        self.append(title)

        # Theme buttons in a FlowBox
        flowbox = Gtk.FlowBox()
        flowbox.set_homogeneous(True)
        flowbox.set_max_children_per_line(3)
        flowbox.set_min_children_per_line(2)
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_row_spacing(12)
        flowbox.set_column_spacing(12)
        flowbox.set_margin_top(16)

        for label, theme in self.THEMES:
            btn = Gtk.Button(label=label)
            btn.add_css_class("choice-button")
            btn.set_vexpand(False)
            btn.connect("clicked", self._on_theme_clicked, theme)
            flowbox.append(btn)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(flowbox)
        self.append(scrolled)

        # Custom theme entry
        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_box.set_margin_top(12)

        self.custom_entry = Gtk.Entry()
        self.custom_entry.set_placeholder_text(_("Eller skriv ditt eget tema..."))
        self.custom_entry.set_hexpand(True)
        custom_box.append(self.custom_entry)

        custom_btn = Gtk.Button(label=_("Starta!"))
        custom_btn.add_css_class("suggested-action")
        custom_btn.connect("clicked", self._on_custom_theme)
        custom_box.append(custom_btn)

        self.append(custom_box)

    def _on_theme_clicked(self, button, theme):
        self.window.show_story(self.window.current_profile, theme)

    def _on_custom_theme(self, button):
        theme = self.custom_entry.get_text().strip()
        if theme:
            self.window.show_story(self.window.current_profile, theme)
