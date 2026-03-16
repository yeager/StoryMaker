"""Child profile data model."""

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChildProfile:
    """Represents a child user's profile."""

    id: Optional[int] = None
    name: str = ""
    age: int = 8
    interests: list[str] = field(default_factory=list)
    language: str = "sv"
    avatar_emoji: str = "🧒"
    created_at: Optional[str] = None

    def age_band(self) -> str:
        """Return the age band for content adaptation."""
        if self.age <= 8:
            return "young"
        elif self.age <= 10:
            return "middle"
        return "older"

    def interests_text(self) -> str:
        """Return interests as comma-separated string."""
        return ", ".join(self.interests)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "interests": self.interests,
            "language": self.language,
            "avatar_emoji": self.avatar_emoji,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChildProfile":
        interests = data.get("interests", [])
        if isinstance(interests, str):
            interests = json.loads(interests)
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            age=data.get("age", 8),
            interests=interests,
            language=data.get("language", "sv"),
            avatar_emoji=data.get("avatar_emoji", "🧒"),
            created_at=data.get("created_at"),
        )
