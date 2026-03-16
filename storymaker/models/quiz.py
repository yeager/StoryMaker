"""Quiz data models for reading comprehension."""

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QuizQuestion:
    """A single quiz question."""
    question: str
    options: list[str] = field(default_factory=list)
    correct_index: int = 0
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuizQuestion":
        return cls(
            question=data["question"],
            options=data.get("options", []),
            correct_index=data.get("correct_index", 0),
            explanation=data.get("explanation", ""),
        )


@dataclass
class QuizResult:
    """Result of a quiz attempt."""
    id: Optional[int] = None
    story_id: Optional[int] = None
    profile_id: Optional[int] = None
    questions: list[QuizQuestion] = field(default_factory=list)
    answers: list[int] = field(default_factory=list)
    score: int = 0
    total: int = 0
    completed_at: Optional[str] = None

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.score / self.total) * 100

    def to_json(self) -> str:
        return json.dumps({
            "questions": [q.to_dict() for q in self.questions],
            "answers": self.answers,
            "score": self.score,
            "total": self.total,
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, data_str: str, **kwargs) -> "QuizResult":
        data = json.loads(data_str)
        return cls(
            questions=[QuizQuestion.from_dict(q) for q in data.get("questions", [])],
            answers=data.get("answers", []),
            score=data.get("score", 0),
            total=data.get("total", 0),
            **kwargs,
        )
