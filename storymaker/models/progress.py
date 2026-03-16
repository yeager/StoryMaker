"""Progress tracking model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Progress:
    """Tracks a child's reading progress and achievements."""
    id: Optional[int] = None
    profile_id: Optional[int] = None
    total_stories: int = 0
    completed_stories: int = 0
    total_quizzes: int = 0
    avg_score: float = 0.0
    words_read: int = 0
    chapters_read: int = 0
    last_active: Optional[str] = None

    @property
    def stories_completion_rate(self) -> float:
        if self.total_stories == 0:
            return 0.0
        return (self.completed_stories / self.total_stories) * 100

    @property
    def reading_level(self) -> str:
        """Simple reading level based on activity."""
        if self.words_read < 500:
            return _("Nybörjare")
        elif self.words_read < 2000:
            return _("Läsare")
        elif self.words_read < 5000:
            return _("Bokmal")
        return _("Mästare")
