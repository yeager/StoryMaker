"""Service for managing the story library (downloading, caching, etc.)."""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional, Dict

from storymaker.models.story import Story, StoryNode, StoryChoice


class LibraryService:
    """Service for downloading and managing story library."""

    CATALOG_URL = "https://yeager.github.io/storymaker-stories/index.json"
    STORY_BASE_URL = "https://yeager.github.io/storymaker-stories/stories"
    
    def __init__(self):
        self.local_stories_dir = Path.home() / ".local/share/storymaker/stories"
        self.local_stories_dir.mkdir(parents=True, exist_ok=True)

    def fetch_catalog(self) -> List[Dict]:
        """Fetch the story catalog from GitHub Pages."""
        try:
            with urllib.request.urlopen(self.CATALOG_URL) as response:
                data = response.read().decode('utf-8')
                catalog = json.loads(data)
                return catalog.get("stories", [])
        except Exception as e:
            raise Exception(f"Failed to fetch catalog: {e}")

    def download_story(self, story_info: Dict) -> None:
        """Download a story and save it locally."""
        story_id = story_info["id"]
        language = story_info["language"]
        
        # Construct download URL
        story_url = f"{self.STORY_BASE_URL}/{language}/{story_id}.json"
        
        try:
            with urllib.request.urlopen(story_url) as response:
                story_data = response.read().decode('utf-8')
                
            # Save to local directory
            local_path = self.local_stories_dir / f"{story_id}.json"
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(story_data)
                
        except Exception as e:
            raise Exception(f"Failed to download story: {e}")

    def get_downloaded_stories(self) -> List[Dict]:
        """Get list of downloaded stories with metadata."""
        stories = []
        
        for json_file in self.local_stories_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                    
                # Extract metadata
                story_info = {
                    "id": story_data.get("id"),
                    "title": story_data.get("title"),
                    "description": story_data.get("description"),
                    "language": story_data.get("language"),
                    "age_group": story_data.get("age_group"),
                    "author": story_data.get("author"),
                    "local_path": str(json_file)
                }
                stories.append(story_info)
                
            except Exception as e:
                print(f"Error reading story file {json_file}: {e}")
                continue
                
        return stories

    def load_downloaded_story(self, story_id: str) -> Optional[Story]:
        """Load a downloaded story as a Story object."""
        story_path = self.local_stories_dir / f"{story_id}.json"
        
        if not story_path.exists():
            return None
            
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
                
            # Convert to Story object
            story = Story(
                title=story_data.get("title", ""),
                theme=story_data.get("title", "")  # Use title as theme for library stories
            )
            
            # Convert chapters to nodes
            chapters = story_data.get("chapters", [])
            for i, chapter_data in enumerate(chapters):
                node_id = f"chapter_{i+1}"
                if i == 0:
                    node_id = "start"  # First chapter is the start node
                
                choices = []
                for choice_data in chapter_data.get("choices", []):
                    choice = StoryChoice(
                        text=choice_data.get("text", ""),
                        emoji=choice_data.get("emoji", ""),
                        next_node_id=f"chapter_{i+2}" if i < len(chapters) - 1 else None
                    )
                    choices.append(choice)
                
                node = StoryNode(
                    node_id=node_id,
                    text=chapter_data.get("text", ""),
                    choices=choices,
                    keywords=chapter_data.get("keywords", []),
                    is_ending=(i == len(chapters) - 1),
                    chapter=i + 1
                )
                
                story.add_node(node)
                
            return story
            
        except Exception as e:
            print(f"Error loading story {story_id}: {e}")
            return None

    def delete_downloaded_story(self, story_id: str) -> None:
        """Delete a downloaded story."""
        story_path = self.local_stories_dir / f"{story_id}.json"
        
        if story_path.exists():
            story_path.unlink()

    def is_story_downloaded(self, story_id: str) -> bool:
        """Check if a story is already downloaded."""
        story_path = self.local_stories_dir / f"{story_id}.json"
        return story_path.exists()