"""Story reading view with text, pictograms, and choices."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk, GdkPixbuf

from storymaker.services.arasaac_client import ArasaacClient
from storymaker.utils.async_helper import run_async
from storymaker.utils.i18n import _


class StoryView(Gtk.Box):
    """Main story reading interface with text, pictograms, and choices."""

    def __init__(self, window, profile, theme, preloaded_story=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self.profile = profile
        self.theme = theme
        self.engine = window.engine
        self.tts = window.tts
        self.arasaac = ArasaacClient()
        self.chapter_number = 0
        self.preloaded_story = preloaded_story

        self._build_ui()
        self._start_story()

    def _build_ui(self):
        """Build the story view UI."""
        # Header
        header = Adw.HeaderBar()

        # TTS button
        if self.tts.is_available:
            tts_btn = Gtk.Button(icon_name="audio-speakers-symbolic")
            tts_btn.set_tooltip_text(_("Read up"))
            tts_btn.connect("clicked", self._on_tts_clicked)
            self._stop_btn = Gtk.Button(icon_name="media-playback-stop-symbolic")
            self._stop_btn.set_tooltip_text(_("Stop"))
            self._stop_btn.connect("clicked", lambda _: self.tts.stop())
            header.pack_end(self._stop_btn)
            header.pack_end(tts_btn)

        # Home button
        home_btn = Gtk.Button(icon_name="go-home-symbolic")
        home_btn.set_tooltip_text(_("Home"))
        home_btn.connect("clicked", lambda _: self.window.go_home())
        header.pack_end(home_btn)

        self.append(header)

        # Scrollable content
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_vexpand(True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.content_box.set_margin_top(24)
        self.content_box.set_margin_bottom(24)
        self.content_box.set_margin_start(32)
        self.content_box.set_margin_end(32)

        # Chapter indicator
        self.chapter_label = Gtk.Label()
        self.chapter_label.add_css_class("chapter-indicator")
        self.content_box.append(self.chapter_label)

        # Story text area
        self.story_label = Gtk.Label()
        self.story_label.set_wrap(True)
        self.story_label.set_wrap_mode(2)  # WORD_CHAR
        self.story_label.set_max_width_chars(60)
        self.story_label.set_natural_wrap_mode(True) if hasattr(self.story_label, "set_natural_wrap_mode") else None
        self.story_label.set_xalign(0)
        self.story_label.add_css_class("story-text")
        self.story_label.set_selectable(True)
        self.content_box.append(self.story_label)

        # Pictogram area
        self.pictogram_box = Gtk.FlowBox()
        self.pictogram_box.set_homogeneous(False)
        self.pictogram_box.set_max_children_per_line(8)
        self.pictogram_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pictogram_box.set_row_spacing(4)
        self.pictogram_box.set_column_spacing(8)
        self.content_box.append(self.pictogram_box)

        # Choices area
        self.choices_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.choices_box.set_margin_top(16)
        self.content_box.append(self.choices_box)

        # Loading spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.content_box.append(self.spinner)

        self.scroll.set_child(self.content_box)
        self.append(self.scroll)

    def _start_story(self):
        """Start the story (either generate new or load preloaded)."""
        if self.preloaded_story:
            # Use preloaded story from library
            self.engine.story = self.preloaded_story
            self.chapter_number = 1
            self._display_current_node()
            # Save to database
            self.window.db.save_story(self.preloaded_story)
        else:
            # Generate new story
            self._show_loading(True)

            def generate():
                return self.engine.start_story(self.profile, self.theme)

            def on_result(story):
                self._show_loading(False)
                if story:
                    self.chapter_number = 1
                    self._display_current_node()
                    # Save to database
                    self.window.db.save_story(story)
                else:
                    self._show_error(_("Could not create the story. Try again!"))

            def on_error(e):
                self._show_loading(False)
                self._show_error(str(e))

            run_async(generate, on_result, on_error)

    def _display_current_node(self):
        """Display the current story node."""
        node = self.engine.current_story.current_node()
        if not node:
            return

        # Update chapter label
        if node.is_ending:
            self.chapter_label.set_text(_("Slutet"))
        else:
            self.chapter_label.set_text(f"{_('Kapitel')} {node.chapter}")

        # Update story text
        self.story_label.set_text(node.text)

        # Show pictograms
        self._display_pictograms(node.keywords)

        # Show choices or ending
        self._clear_choices()
        if node.is_ending:
            self._show_ending()
        else:
            self._display_choices(node.choices)

        # Scroll to top
        GLib.idle_add(self._scroll_to_top)

    def _display_pictograms(self, keywords):
        """Display pictogram images/emojis for keywords."""
        # Clear existing
        while child := self.pictogram_box.get_first_child():
            self.pictogram_box.remove(child)

        for keyword in keywords:
            result = self.arasaac.get_pictogram_or_emoji(keyword, self.profile.language)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_halign(Gtk.Align.CENTER)

            image_path = result.get("image_path")
            if image_path:
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 64, 64, True)
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    img = Gtk.Picture.new_for_paintable(texture)
                    img.set_size_request(64, 64)
                    img.add_css_class("pictogram-image")
                    box.append(img)
                except Exception:
                    emoji = result.get("emoji", "")
                    if emoji:
                        lbl = Gtk.Label(label=emoji)
                        lbl.set_markup(f'<span size="xx-large">{emoji}</span>')
                        box.append(lbl)
            else:
                emoji = result.get("emoji", "")
                if emoji:
                    lbl = Gtk.Label(label=emoji)
                    lbl.set_markup(f'<span size="xx-large">{emoji}</span>')
                    box.append(lbl)

            # Keyword label under the pictogram
            kw_label = Gtk.Label(label=keyword)
            kw_label.add_css_class("caption")
            box.append(kw_label)

            self.pictogram_box.append(box)

    def _display_choices(self, choices):
        """Display choice buttons."""
        choices_label = Gtk.Label(label=_("What will happen next?"))
        choices_label.add_css_class("title-4")
        self.choices_box.append(choices_label)

        for i, choice in enumerate(choices):
            label = f"{choice.emoji} {choice.text}" if choice.emoji else choice.text
            btn = Gtk.Button(label=label)
            btn.add_css_class("choice-button")
            btn.connect("clicked", self._on_choice_clicked, i)
            self.choices_box.append(btn)

    def _on_choice_clicked(self, button, choice_index):
        """Handle a choice being made."""
        self._show_loading(True)
        self._clear_choices()

        def generate():
            return self.engine.make_choice(choice_index)

        def on_result(node):
            self._show_loading(False)
            if node:
                self.chapter_number += 1
                self._display_current_node()
                # Save progress
                self.window.db.save_story(self.engine.current_story)
                # Update progress
                progress = self.window.db.get_progress(self.profile.id)
                progress.chapters_read += 1
                progress.words_read += len(node.text.split())
                self.window.db.update_progress(progress)
            else:
                self._show_error(_("Something went wrong. Try again!"))

        def on_error(e):
            self._show_loading(False)
            self._show_error(str(e))

        run_async(generate, on_result, on_error)

    def _show_ending(self):
        """Show the ending UI with quiz option."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(16)

        congrats = Gtk.Label(label=_("🎉 Congratulations! You have finished the story!"))
        congrats.add_css_class("title-3")
        box.append(congrats)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)

        quiz_btn = Gtk.Button(label=_("📝 Take the quiz!"))
        quiz_btn.add_css_class("suggested-action")
        quiz_btn.add_css_class("pill")
        quiz_btn.connect("clicked", self._on_quiz_clicked)
        btn_box.append(quiz_btn)

        home_btn = Gtk.Button(label=_("🏠 Back home"))
        home_btn.add_css_class("pill")
        home_btn.connect("clicked", lambda _: self.window.go_home())
        btn_box.append(home_btn)

        box.append(btn_box)
        self.choices_box.append(box)

        # Update progress
        progress = self.window.db.get_progress(self.profile.id)
        progress.completed_stories += 1
        self.window.db.update_progress(progress)

    def _on_quiz_clicked(self, button):
        """Start the quiz."""
        self.window.show_quiz(self.engine.current_story)

    def _on_tts_clicked(self, button):
        """Read the current text aloud."""
        if self.tts.is_speaking:
            self.tts.stop()
        else:
            node = self.engine.current_story.current_node()
            if node:
                self.tts.speak(node.text, self.profile.language)

    def _clear_choices(self):
        """Remove all choice buttons."""
        while child := self.choices_box.get_first_child():
            self.choices_box.remove(child)

    def _show_loading(self, loading):
        """Show or hide loading spinner."""
        self.spinner.set_spinning(loading)
        self.spinner.set_visible(loading)

    def _show_error(self, message):
        """Show an error message."""
        label = Gtk.Label(label=message)
        label.add_css_class("error")
        self.choices_box.append(label)

        retry_btn = Gtk.Button(label=_("Try again"))
        retry_btn.add_css_class("suggested-action")
        retry_btn.connect("clicked", lambda _: self._start_story())
        self.choices_box.append(retry_btn)

    def _scroll_to_top(self):
        """Scroll to top of content."""
        adj = self.scroll.get_vadjustment()
        adj.set_value(0)
