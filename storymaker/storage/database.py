"""SQLite database management."""

import sqlite3
import json
from pathlib import Path
from typing import Optional

from storymaker.config import DB_PATH
from storymaker.models.child_profile import ChildProfile
from storymaker.models.progress import Progress


class Database:
    """Manages the SQLite database for StoryMaker."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.conn = None

    def initialize(self):
        """Create the database and tables."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        """Create all required tables."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL DEFAULT 8,
                interests TEXT NOT NULL DEFAULT '[]',
                language TEXT NOT NULL DEFAULT 'sv',
                avatar_emoji TEXT NOT NULL DEFAULT '🧒',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                tree_json TEXT NOT NULL DEFAULT '{}',
                is_complete INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            );

            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                profile_id INTEGER NOT NULL,
                quiz_json TEXT NOT NULL DEFAULT '{}',
                score INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id),
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            );

            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER UNIQUE NOT NULL,
                total_stories INTEGER NOT NULL DEFAULT 0,
                completed_stories INTEGER NOT NULL DEFAULT 0,
                total_quizzes INTEGER NOT NULL DEFAULT 0,
                avg_score REAL NOT NULL DEFAULT 0.0,
                words_read INTEGER NOT NULL DEFAULT 0,
                chapters_read INTEGER NOT NULL DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            );
        """)
        self.conn.commit()

    # --- Profile CRUD ---

    def save_profile(self, profile: ChildProfile) -> int:
        """Insert or update a child profile."""
        interests_json = json.dumps(profile.interests, ensure_ascii=False)
        if profile.id:
            self.conn.execute(
                "UPDATE profiles SET name=?, age=?, interests=?, language=?, avatar_emoji=? WHERE id=?",
                (profile.name, profile.age, interests_json, profile.language, profile.avatar_emoji, profile.id),
            )
        else:
            cursor = self.conn.execute(
                "INSERT INTO profiles (name, age, interests, language, avatar_emoji) VALUES (?, ?, ?, ?, ?)",
                (profile.name, profile.age, interests_json, profile.language, profile.avatar_emoji),
            )
            profile.id = cursor.lastrowid
        self.conn.commit()
        return profile.id

    def get_profiles(self) -> list[ChildProfile]:
        """Get all child profiles."""
        rows = self.conn.execute("SELECT * FROM profiles ORDER BY name").fetchall()
        return [ChildProfile.from_dict(dict(row)) for row in rows]

    def get_profile(self, profile_id: int) -> Optional[ChildProfile]:
        """Get a single profile by ID."""
        row = self.conn.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()
        if row:
            return ChildProfile.from_dict(dict(row))
        return None

    def delete_profile(self, profile_id: int):
        """Delete a profile and all associated data."""
        self.conn.execute("DELETE FROM quiz_results WHERE profile_id=?", (profile_id,))
        self.conn.execute("DELETE FROM stories WHERE profile_id=?", (profile_id,))
        self.conn.execute("DELETE FROM progress WHERE profile_id=?", (profile_id,))
        self.conn.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
        self.conn.commit()

    # --- Story CRUD ---

    def save_story(self, story) -> int:
        """Save a story."""
        from storymaker.models.story import Story
        if story.id:
            self.conn.execute(
                "UPDATE stories SET title=?, tree_json=?, is_complete=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (story.title, story.to_json(), story.is_complete, story.id),
            )
        else:
            cursor = self.conn.execute(
                "INSERT INTO stories (profile_id, title, tree_json, is_complete) VALUES (?, ?, ?, ?)",
                (story.profile_id, story.title, story.to_json(), story.is_complete),
            )
            story.id = cursor.lastrowid
        self.conn.commit()
        return story.id

    def get_stories(self, profile_id: int) -> list:
        """Get all stories for a profile."""
        from storymaker.models.story import Story
        rows = self.conn.execute(
            "SELECT * FROM stories WHERE profile_id=? ORDER BY updated_at DESC",
            (profile_id,),
        ).fetchall()
        stories = []
        for row in rows:
            d = dict(row)
            story = Story.from_json(d["tree_json"], story_id=d["id"], profile_id=d["profile_id"])
            story.created_at = d["created_at"]
            stories.append(story)
        return stories

    def get_story(self, story_id: int):
        """Get a single story."""
        from storymaker.models.story import Story
        row = self.conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
        if row:
            d = dict(row)
            story = Story.from_json(d["tree_json"], story_id=d["id"], profile_id=d["profile_id"])
            story.created_at = d["created_at"]
            return story
        return None

    # --- Quiz Results ---

    def save_quiz_result(self, result) -> int:
        """Save a quiz result."""
        cursor = self.conn.execute(
            "INSERT INTO quiz_results (story_id, profile_id, quiz_json, score, total) VALUES (?, ?, ?, ?, ?)",
            (result.story_id, result.profile_id, result.to_json(), result.score, result.total),
        )
        result.id = cursor.lastrowid
        self.conn.commit()
        return result.id

    def get_quiz_results(self, profile_id: int) -> list:
        """Get all quiz results for a profile."""
        return self.conn.execute(
            "SELECT * FROM quiz_results WHERE profile_id=? ORDER BY completed_at DESC",
            (profile_id,),
        ).fetchall()

    # --- Progress ---

    def get_progress(self, profile_id: int) -> Progress:
        """Get or create progress for a profile."""
        row = self.conn.execute(
            "SELECT * FROM progress WHERE profile_id=?", (profile_id,)
        ).fetchone()
        if row:
            d = dict(row)
            return Progress(**d)
        # Create new progress entry
        self.conn.execute(
            "INSERT INTO progress (profile_id) VALUES (?)", (profile_id,)
        )
        self.conn.commit()
        return Progress(profile_id=profile_id)

    def update_progress(self, progress: Progress):
        """Update progress stats."""
        self.conn.execute(
            """UPDATE progress SET total_stories=?, completed_stories=?,
               total_quizzes=?, avg_score=?, words_read=?, chapters_read=?,
               last_active=CURRENT_TIMESTAMP WHERE profile_id=?""",
            (progress.total_stories, progress.completed_stories,
             progress.total_quizzes, progress.avg_score, progress.words_read,
             progress.chapters_read, progress.profile_id),
        )
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
