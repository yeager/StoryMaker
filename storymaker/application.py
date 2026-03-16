"""Main application class for StoryMaker."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

from storymaker.config import APP_ID, APP_NAME, APP_VERSION
from storymaker.storage.database import Database


class StoryMakerApp(Adw.Application):
    """The main StoryMaker application."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.db = None

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Initialize database
        self.db = Database()
        self.db.initialize()

        # Load CSS
        self._load_css()

        # Register actions
        self._setup_actions()

    def do_activate(self):
        from storymaker.ui.window import StoryMakerWindow
        win = self.props.active_window
        if not win:
            win = StoryMakerWindow(application=self)
        win.present()

    def _load_css(self):
        """Load custom CSS for child-friendly styling."""
        css_provider = Gtk.CssProvider()
        css = """
        .story-text {
            font-size: 20px;
            font-family: "Comic Neue", "Comic Sans MS", sans-serif;
            line-height: 1.8;
            padding: 16px;
        }
        .story-title {
            font-size: 28px;
            font-weight: bold;
            font-family: "Comic Neue", "Comic Sans MS", sans-serif;
        }
        .choice-button {
            font-size: 18px;
            padding: 16px 24px;
            margin: 8px;
            border-radius: 16px;
            font-family: "Comic Neue", "Comic Sans MS", sans-serif;
        }
        .choice-button:hover {
            background: alpha(@accent_color, 0.2);
        }
        .quiz-question {
            font-size: 20px;
            font-weight: bold;
            padding: 12px;
            font-family: "Comic Neue", "Comic Sans MS", sans-serif;
        }
        .quiz-answer {
            font-size: 18px;
            padding: 12px 20px;
            margin: 6px;
            border-radius: 12px;
        }
        .quiz-correct {
            background: alpha(#4caf50, 0.3);
        }
        .quiz-incorrect {
            background: alpha(#f44336, 0.3);
        }
        .pictogram-image {
            margin: 4px;
        }
        .welcome-title {
            font-size: 36px;
            font-weight: bold;
            font-family: "Comic Neue", "Comic Sans MS", sans-serif;
        }
        .welcome-subtitle {
            font-size: 18px;
            font-family: "Comic Neue", "Comic Sans MS", sans-serif;
        }
        .profile-card {
            padding: 16px;
            border-radius: 16px;
            margin: 8px;
        }
        .progress-bar {
            min-height: 12px;
            border-radius: 6px;
        }
        .chapter-indicator {
            font-size: 14px;
            opacity: 0.7;
        }
        .score-label {
            font-size: 24px;
            font-weight: bold;
        }
        """
        css_provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display() if hasattr(self, 'get_display') else
            __import__('gi.repository', fromlist=['Gdk']).Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _setup_actions(self):
        """Register application actions."""
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def _on_about(self, action, param):
        """Show the about dialog."""
        about = Adw.AboutDialog(
            application_name=APP_NAME,
            application_icon=APP_ID,
            developer_name="StoryMaker Team",
            version=APP_VERSION,
            comments=_("Interactive stories with AI and pictograms for reading comprehension training"),
            website="https://github.com/yeager/StoryMaker",
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(self.props.active_window)
