"""Story data models for the branching narrative engine."""

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StoryChoice:
    """A choice the reader can make at a decision point."""
    text: str
    emoji: str = ""
    next_node_id: Optional[str] = None


@dataclass
class StoryNode:
    """A single node in the story tree."""
    node_id: str
    text: str
    choices: list[StoryChoice] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    is_ending: bool = False
    chapter: int = 1

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "text": self.text,
            "choices": [
                {"text": c.text, "emoji": c.emoji, "next_node_id": c.next_node_id}
                for c in self.choices
            ],
            "keywords": self.keywords,
            "is_ending": self.is_ending,
            "chapter": self.chapter,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StoryNode":
        choices = [
            StoryChoice(
                text=c["text"],
                emoji=c.get("emoji", ""),
                next_node_id=c.get("next_node_id"),
            )
            for c in data.get("choices", [])
        ]
        return cls(
            node_id=data["node_id"],
            text=data["text"],
            choices=choices,
            keywords=data.get("keywords", []),
            is_ending=data.get("is_ending", False),
            chapter=data.get("chapter", 1),
        )


@dataclass
class Story:
    """A complete branching story."""
    id: Optional[int] = None
    profile_id: Optional[int] = None
    title: str = ""
    theme: str = ""
    nodes: dict[str, StoryNode] = field(default_factory=dict)
    current_node_id: str = "start"
    is_complete: bool = False
    created_at: Optional[str] = None

    def current_node(self) -> Optional[StoryNode]:
        return self.nodes.get(self.current_node_id)

    def add_node(self, node: StoryNode):
        self.nodes[node.node_id] = node

    def chapter_count(self) -> int:
        if not self.nodes:
            return 0
        return max(n.chapter for n in self.nodes.values())

    def to_json(self) -> str:
        return json.dumps({
            "title": self.title,
            "theme": self.theme,
            "current_node_id": self.current_node_id,
            "is_complete": self.is_complete,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, data_str: str, story_id=None, profile_id=None) -> "Story":
        data = json.loads(data_str)
        nodes = {
            k: StoryNode.from_dict(v)
            for k, v in data.get("nodes", {}).items()
        }
        return cls(
            id=story_id,
            profile_id=profile_id,
            title=data.get("title", ""),
            theme=data.get("theme", ""),
            nodes=nodes,
            current_node_id=data.get("current_node_id", "start"),
            is_complete=data.get("is_complete", False),
        )
