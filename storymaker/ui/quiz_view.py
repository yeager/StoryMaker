"""Quiz view for reading comprehension testing."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib

from storymaker.models.quiz import QuizResult
from storymaker.utils.async_helper import run_async


class QuizView(Gtk.Box):
    """Reading comprehension quiz interface."""

    def __init__(self, window, story):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self.story = story
        self.engine = window.engine
        self.questions = []
        self.current_question = 0
        self.score = 0
        self.answers = []

        self._build_ui()
        self._generate_quiz()

    def _build_ui(self):
        """Build the quiz UI."""
        header = Adw.HeaderBar()
        self.append(header)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.content.set_margin_top(24)
        self.content.set_margin_bottom(24)
        self.content.set_margin_start(32)
        self.content.set_margin_end(32)
        self.content.set_vexpand(True)

        # Title
        title = Gtk.Label(label=_("📝 Reading comprehension"))
        title.add_css_class("title-2")
        self.content.append(title)

        # Progress indicator
        self.progress_label = Gtk.Label()
        self.progress_label.add_css_class("dim-label")
        self.content.append(self.progress_label)

        # Question area
        self.question_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.question_box.set_vexpand(True)
        self.content.append(self.question_box)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.content.append(self.spinner)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.content)
        self.append(scroll)

    def _generate_quiz(self):
        """Generate quiz questions from the story."""
        self.spinner.set_spinning(True)
        self.spinner.set_visible(True)

        def generate():
            return self.engine.generate_quiz(num_questions=3)

        def on_result(questions):
            self.spinner.set_spinning(False)
            self.spinner.set_visible(False)
            self.questions = questions
            if questions:
                self._show_question()
            else:
                self._show_error(_("Could not create quiz. Please try again!"))

        def on_error(e):
            self.spinner.set_spinning(False)
            self.spinner.set_visible(False)
            self._show_error(str(e))

        run_async(generate, on_result, on_error)

    def _show_question(self):
        """Display the current question."""
        # Clear question box
        while child := self.question_box.get_first_child():
            self.question_box.remove(child)

        if self.current_question >= len(self.questions):
            self._show_results()
            return

        q = self.questions[self.current_question]
        self.progress_label.set_text(
            f"{_("Question")} {self.current_question + 1} / {len(self.questions)}"
        )

        # Question text
        q_label = Gtk.Label(label=q.question)
        q_label.add_css_class("quiz-question")
        q_label.set_wrap(True)
        q_label.set_xalign(0)
        self.question_box.append(q_label)

        # Answer options
        for i, option in enumerate(q.options):
            btn = Gtk.Button(label=option)
            btn.add_css_class("quiz-answer")
            btn.connect("clicked", self._on_answer, i)
            self.question_box.append(btn)

    def _on_answer(self, button, answer_index):
        """Handle an answer selection."""
        q = self.questions[self.current_question]
        self.answers.append(answer_index)
        is_correct = answer_index == q.correct_index

        if is_correct:
            self.score += 1
            button.add_css_class("quiz-correct")
        else:
            button.add_css_class("quiz-incorrect")
            # Highlight correct answer
            correct_idx = q.correct_index
            children = []
            child = self.question_box.get_first_child()
            while child:
                children.append(child)
                child = child.get_next_sibling()
            # Options start after the question label
            if correct_idx + 1 < len(children):
                children[correct_idx + 1].add_css_class("quiz-correct")

        # Disable all buttons
        child = self.question_box.get_first_child()
        while child:
            if isinstance(child, Gtk.Button):
                child.set_sensitive(False)
            child = child.get_next_sibling()

        # Show explanation
        if q.explanation:
            exp_label = Gtk.Label(label=f"💡 {q.explanation}")
            exp_label.set_wrap(True)
            exp_label.set_xalign(0)
            exp_label.set_margin_top(8)
            self.question_box.append(exp_label)

        # Next button
        GLib.timeout_add(1500, self._next_question)

    def _next_question(self):
        """Move to the next question."""
        self.current_question += 1
        self._show_question()
        return False  # Don't repeat timeout

    def _show_results(self):
        """Show quiz results."""
        while child := self.question_box.get_first_child():
            self.question_box.remove(child)

        self.progress_label.set_text(_("Results"))

        # Score display
        score_label = Gtk.Label()
        score_label.set_markup(
            f'<span size="xx-large" weight="bold">{self.score} / {len(self.questions)}</span>'
        )
        score_label.add_css_class("score-label")
        self.question_box.append(score_label)

        # Encouragement message
        percentage = (self.score / len(self.questions)) * 100 if self.questions else 0
        if percentage >= 80:
            msg = _("🌟 Fantastic! You understood the story very well!")
        elif percentage >= 50:
            msg = _("👍 Good job! You understood most of it!")
        else:
            msg = _("💪 Nice try! Read the story again and then try!")

        msg_label = Gtk.Label(label=msg)
        msg_label.add_css_class("title-4")
        msg_label.set_wrap(True)
        self.question_box.append(msg_label)

        # Save quiz result
        self._save_result()

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(16)

        home_btn = Gtk.Button(label=_("🏠 Home"))
        home_btn.add_css_class("pill")
        home_btn.connect("clicked", lambda _: self.window.go_home())
        btn_box.append(home_btn)

        self.question_box.append(btn_box)

    def _save_result(self):
        """Save quiz result to database."""
        profile = self.window.current_profile
        if not profile:
            return

        result = QuizResult(
            story_id=self.story.id,
            profile_id=profile.id,
            questions=self.questions,
            answers=self.answers,
            score=self.score,
            total=len(self.questions),
        )
        self.window.db.save_quiz_result(result)

        # Update progress
        progress = self.window.db.get_progress(profile.id)
        progress.total_quizzes += 1
        # Recalculate average score
        all_results = self.window.db.get_quiz_results(profile.id)
        if all_results:
            total_score = sum(r["score"] for r in all_results)
            total_questions = sum(r["total"] for r in all_results)
            progress.avg_score = (total_score / total_questions * 100) if total_questions else 0
        self.window.db.update_progress(progress)

    def _show_error(self, message):
        """Show error in quiz area."""
        label = Gtk.Label(label=message)
        label.add_css_class("error")
        self.question_box.append(label)
