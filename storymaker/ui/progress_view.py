"""Progress tracking dashboard view."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class ProgressView(Gtk.Box):
    """Progress dashboard showing reading stats and achievements."""

    def __init__(self, window, profile):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self.profile = profile

        self._build_ui()

    def _build_ui(self):
        """Build the progress dashboard."""
        header = Adw.HeaderBar()
        self.append(header)

        progress = self.window.db.get_progress(self.profile.id)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(32)
        content.set_margin_end(32)

        # Profile header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        avatar = Gtk.Label()
        avatar.set_markup(f'<span size="xx-large">{self.profile.avatar_emoji}</span>')
        header_box.append(avatar)

        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_label = Gtk.Label(label=self.profile.name)
        name_label.add_css_class("title-2")
        name_label.set_xalign(0)
        name_box.append(name_label)

        level_label = Gtk.Label(label=f"{_('Nivå')}: {progress.reading_level}")
        level_label.set_xalign(0)
        level_label.add_css_class("dim-label")
        name_box.append(level_label)

        header_box.append(name_box)
        content.append(header_box)

        # Stats grid
        stats_group = Adw.PreferencesGroup(title=_("Statistics"))

        # Stories
        stories_row = Adw.ActionRow(
            title=_("Berättelser"),
            subtitle=f"{progress.completed_stories} {_('avslutade')} / {progress.total_stories} {_('totalt')}",
        )
        stories_row.add_prefix(Gtk.Label(label="📚"))
        stats_group.add(stories_row)

        # Words read
        words_row = Adw.ActionRow(
            title=_("Ord lästa"),
            subtitle=str(progress.words_read),
        )
        words_row.add_prefix(Gtk.Label(label="📖"))
        stats_group.add(words_row)

        # Chapters
        chapters_row = Adw.ActionRow(
            title=_("Kapitel lästa"),
            subtitle=str(progress.chapters_read),
        )
        chapters_row.add_prefix(Gtk.Label(label="📄"))
        stats_group.add(chapters_row)

        # Quizzes
        quiz_row = Adw.ActionRow(
            title=_("Quiz genomförda"),
            subtitle=str(progress.total_quizzes),
        )
        quiz_row.add_prefix(Gtk.Label(label="📝"))
        stats_group.add(quiz_row)

        # Average score
        score_row = Adw.ActionRow(
            title=_("Genomsnittlig poäng"),
            subtitle=f"{progress.avg_score:.0f}%",
        )
        score_row.add_prefix(Gtk.Label(label="⭐"))
        stats_group.add(score_row)

        content.append(stats_group)

        # Reading progress bar
        progress_group = Adw.PreferencesGroup(title=_("Läsframsteg"))

        progress_bar = Gtk.ProgressBar()
        progress_bar.add_css_class("progress-bar")
        words_goal = 5000
        fraction = min(progress.words_read / words_goal, 1.0)
        progress_bar.set_fraction(fraction)
        progress_bar.set_text(f"{progress.words_read} / {words_goal} {_('ord')}")
        progress_bar.set_show_text(True)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        progress_box.set_margin_top(8)
        progress_box.set_margin_bottom(8)
        goal_label = Gtk.Label(label=_("Mål: Läs 5000 ord!"))
        goal_label.set_xalign(0)
        progress_box.append(goal_label)
        progress_box.append(progress_bar)

        progress_group.add(progress_box)
        content.append(progress_group)

        # Recent stories
        stories = self.window.db.get_stories(self.profile.id)
        if stories:
            stories_group = Adw.PreferencesGroup(title=_("Senaste berättelser"))
            for story in stories[:5]:
                status = "✅" if story.is_complete else "📖"
                row = Adw.ActionRow(
                    title=f"{status} {story.title}",
                    subtitle=f"{story.chapter_count()} {_('kapitel')}",
                )
                stories_group.add(row)
            content.append(stories_group)

        scroll.set_child(content)
        self.append(scroll)
