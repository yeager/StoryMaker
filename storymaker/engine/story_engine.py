"""Story engine - orchestrates AI generation and story branching."""

from typing import Optional

from storymaker.models.child_profile import ChildProfile
from storymaker.models.story import Story, StoryNode
from storymaker.models.quiz import QuizQuestion
from storymaker.services.ai_provider import AIProvider, create_provider


class StoryEngine:
    """Orchestrates interactive story generation and progression."""

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or create_provider()
        self.current_story: Optional[Story] = None
        self.current_profile: Optional[ChildProfile] = None

    def set_provider(self, provider_type: str, api_key: str = ""):
        """Switch AI provider."""
        self.provider = create_provider(provider_type, api_key)

    def start_story(self, profile: ChildProfile, theme: str) -> Optional[Story]:
        """Start a new interactive story."""
        self.current_profile = profile
        self.current_story = Story(
            profile_id=profile.id,
            title=theme,
            theme=theme,
        )

        # Generate the first chapter
        node = self.provider.generate_story_segment(
            profile=profile,
            theme=theme,
            chapter=1,
        )

        if node:
            node.node_id = "start"
            self.current_story.add_node(node)
            self.current_story.current_node_id = "start"
            return self.current_story
        return None

    def make_choice(self, choice_index: int) -> Optional[StoryNode]:
        """Process a reader's choice and generate the next segment."""
        if not self.current_story or not self.current_profile:
            return None

        current = self.current_story.current_node()
        if not current or choice_index >= len(current.choices):
            return None

        choice = current.choices[choice_index]
        next_chapter = current.chapter + 1

        # Gather story text so far for context
        previous_text = self._get_story_text()

        # Generate next segment
        node = self.provider.generate_story_segment(
            profile=self.current_profile,
            theme=self.current_story.theme,
            previous_text=previous_text,
            choice_made=choice.text,
            chapter=next_chapter,
        )

        if node:
            node_id = choice.next_node_id or f"chapter_{next_chapter}"
            node.node_id = node_id
            self.current_story.add_node(node)
            self.current_story.current_node_id = node_id

            if node.is_ending:
                self.current_story.is_complete = True

            return node
        return None

    def generate_quiz(self, num_questions: int = 3) -> list[QuizQuestion]:
        """Generate comprehension quiz for the current story."""
        if not self.current_story or not self.current_profile:
            return []

        story_text = self._get_story_text()
        return self.provider.generate_quiz(
            story_text=story_text,
            num_questions=num_questions,
            language=self.current_profile.language,
        )

    def _get_story_text(self) -> str:
        """Get all story text so far."""
        if not self.current_story:
            return ""
        texts = []
        for node in sorted(self.current_story.nodes.values(), key=lambda n: n.chapter):
            texts.append(node.text)
        return "\n\n".join(texts)

    def word_count(self) -> int:
        """Count total words in the current story."""
        text = self._get_story_text()
        return len(text.split())
