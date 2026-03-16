"""Entry point for StoryMaker application."""

import sys

def main():
    """Launch the StoryMaker application."""
    from storymaker.utils.i18n import setup_i18n
    setup_i18n()

    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')

    from storymaker.application import StoryMakerApp
    app = StoryMakerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
