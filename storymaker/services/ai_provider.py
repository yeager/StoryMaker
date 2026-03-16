"""AI provider abstraction for story and quiz generation."""

import json
from abc import ABC, abstractmethod
from typing import Optional

from storymaker.models.child_profile import ChildProfile
from storymaker.models.story import StoryNode, StoryChoice
from storymaker.models.quiz import QuizQuestion
from storymaker.utils.i18n import _


class AIProvider(ABC):
    """Abstract base class for AI text generation providers."""

    @abstractmethod
    def generate_story_segment(
        self,
        profile: ChildProfile,
        theme: str,
        previous_text: str = "",
        choice_made: str = "",
        chapter: int = 1,
    ) -> Optional[StoryNode]:
        """Generate a story segment with choices."""
        pass

    @abstractmethod
    def generate_quiz(
        self,
        story_text: str,
        num_questions: int = 3,
        language: str = "sv",
    ) -> list[QuizQuestion]:
        """Generate comprehension questions for a story segment."""
        pass

    def _build_story_prompt(self, profile, theme, previous_text, choice_made, chapter):
        """Build the prompt for story generation."""
        lang = "svenska" if profile.language == "sv" else "English"
        age_desc = {
            "young": "6-8 år, använd enkla ord och korta meningar",
            "middle": "9-10 år, använd varierat språk",
            "older": "11-12 år, använd rikare språk och mer komplexa handlingar",
        }

        system = f"""Du är en kreativ berättare som skriver interaktiva berättelser för barn.
Skriv på {lang}. Barnet heter {profile.name} och är {profile.age} år.
Anpassa språket för {age_desc.get(profile.age_band(), age_desc['middle'])}.
Barnets intressen: {profile.interests_text() or 'äventyr, djur'}.

VIKTIGT: Svara ALLTID med giltig JSON i detta format:
{{
  "text": "Berättelsetexten här (2-4 stycken)",
  "choices": [
    {{"text": "Valalternativ 1", "emoji": "🌟"}},
    {{"text": "Valalternativ 2", "emoji": "🌊"}},
    {{"text": "Valalternativ 3", "emoji": "🏔️"}}
  ],
  "keywords": ["nyckelord1", "nyckelord2", "nyckelord3"],
  "is_ending": false
}}

Regler:
- Ge alltid exakt 3 valalternativ (om det inte är ett slut)
- keywords ska vara konkreta substantiv/verb som kan illustreras med piktogram
- Sätt is_ending till true om berättelsen ska sluta (efter kapitel 5+)
- Gör berättelsen spännande och pedagogisk
- Inkludera {profile.name} som karaktär i berättelsen"""

        user = f"Tema: {theme}\nKapitel: {chapter}\n"
        if previous_text:
            user += f_("\Previous in the story:\n{previous_text[-500:]}\n")
        if choice_made:
            user += f"\nBarnet valde: {choice_made}\n"
        user += "\nFortsätt berättelsen:"

        return system, user

    def _build_quiz_prompt(self, story_text, num_questions, language):
        """Build the prompt for quiz generation."""
        lang = "svenska" if language == "sv" else "English"
        return f"""Skapa {num_questions} läsförståelsefrågor på {lang} baserat på denna berättelse:

{story_text}

Svara med JSON-array:
[
  {{
    "question": "Frågan här?",
    "options": ["Alternativ A", "Alternativ B", "Alternativ C"],
    "correct_index": 0,
    "explanation": "Förklaring varför svaret är rätt"
  }}
]

Regler:
- Frågorna ska testa förståelse, inte bara minne
- Ge alltid exakt 3 svarsalternativ
- Anpassa svårigheten till texten
- correct_index är 0-indexerat"""

    def _parse_story_response(self, text: str, chapter: int) -> Optional[StoryNode]:
        """Parse AI response into a StoryNode."""
        try:
            # Try to extract JSON from the response
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)

            node_id = f"chapter_{chapter}" if chapter > 1 else "start"
            choices = [
                StoryChoice(
                    text=c["text"],
                    emoji=c.get("emoji", ""),
                    next_node_id=f"chapter_{chapter + 1}_{i}",
                )
                for i, c in enumerate(data.get("choices", []))
            ]

            return StoryNode(
                node_id=node_id,
                text=data.get("text", ""),
                choices=choices if not data.get("is_ending", False) else [],
                keywords=data.get("keywords", []),
                is_ending=data.get("is_ending", False),
                chapter=chapter,
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Failed to parse AI response: {e}")
            return None

    def _parse_quiz_response(self, text: str) -> list[QuizQuestion]:
        """Parse AI response into quiz questions."""
        try:
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            if isinstance(data, dict) and "questions" in data:
                data = data["questions"]
            return [QuizQuestion.from_dict(q) for q in data]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse quiz response: {e}")
            return []


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def generate_story_segment(self, profile, theme, previous_text="", choice_made="", chapter=1):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            system, user = self._build_story_prompt(profile, theme, previous_text, choice_made, chapter)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.8,
                max_tokens=1000,
            )
            return self._parse_story_response(response.choices[0].message.content, chapter)
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None

    def generate_quiz(self, story_text, num_questions=3, language="sv"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            prompt = self._build_quiz_prompt(story_text, num_questions, language)

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=800,
            )
            return self._parse_quiz_response(response.choices[0].message.content)
        except Exception as e:
            print(f"OpenAI quiz error: {e}")
            return []


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    def generate_story_segment(self, profile, theme, previous_text="", choice_made="", chapter=1):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            system, user = self._build_story_prompt(profile, theme, previous_text, choice_made, chapter)

            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return self._parse_story_response(response.content[0].text, chapter)
        except Exception as e:
            print(f"Anthropic error: {e}")
            return None

    def generate_quiz(self, story_text, num_questions=3, language="sv"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            prompt = self._build_quiz_prompt(story_text, num_questions, language)

            response = client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_quiz_response(response.content[0].text)
        except Exception as e:
            print(f"Anthropic quiz error: {e}")
            return []


class DemoProvider(AIProvider):
    """Demo provider with pre-built stories for testing without API keys."""

    def generate_story_segment(self, profile, theme, previous_text="", choice_made="", chapter=1):
        name = profile.name or "Äventyraren"
        stories = {
            1: {
                "text": f_("{name} stood at the edge of the Enchanted Forest. The trees were so tall that they almost reached the clouds, and between the branches small lights sparkled like stars.\n")Välkommen, {name}!\" ropade en liten uggla som satt på en gren. \"Jag heter Uffe och jag behöver din hjälp. Den magiska boken har försvunnit och utan den kan skogens djur inte prata längre!\"\n\n{name} kände sig modig. Det här var början på ett stort äventyr!",
                "choices": [
                    {"text": "Följ Uffe djupare in i skogen", "emoji": "🌲"},
                    {"text": "Fråga skogens älvor om hjälp", "emoji": "🧚"},
                    {"text": "Leta vid den gamla eken först", "emoji": "🌳"},
                ],
                "keywords": ["skog", "uggla", "bok", "träd", "äventyr"],
            },
            2: {
                "text": f_("{name} continued bravely forward. Suddenly a sound was heard behind a large bush. It was a small fox with a golden key around its neck!")Den här nyckeln öppnar vägen till bokens gömställe,\" viskade räven. \"Men vägen dit är inte lätt. Det finns en bro över en flod, och bron vaktas av ett vänligt men gåtfullt troll.\"\n\n{name} tänkte efter noga. Vad skulle vara bäst att göra?",
                "choices": [
                    {"text": "Gå till bron och prata med trollet", "emoji": "🌉"},
                    {"text": "Simma över floden istället", "emoji": "🏊"},
                    {"text": "Be räven visa en hemlig väg", "emoji": "🦊"},
                ],
                "keywords": ["räv", "nyckel", "bro", "troll", "flod"],
            },
            3: {
                "text": f_("The troll smiled broadly when it saw {name}. \")Välkommen! Jag älskar besök!\" sa trollet. \"Men för att korsa min bro måste du svara på en gåta: Vad har rötter som ingen ser, växer upp men aldrig flyr?\"\n\n{name} tänkte hårt. Plötsligt kom svaret! \"Ett träd!\" ropade {name}.\n\nTrollet klappade i händerna av glädje. \"Rätt svar! Du är verkligen klok. Gå över bron, den magiska boken väntar på dig på andra sidan!\"",
                "choices": [
                    {"text": "Springa över bron direkt", "emoji": "🏃"},
                    {"text": "Tacka trollet och gå försiktigt", "emoji": "🤝"},
                    {"text": "Fråga trollet om det vill följa med", "emoji": "👫"},
                ],
                "keywords": ["troll", "bro", "gåta", "träd", "svar"],
            },
        }

        if chapter >= 5 or (chapter > 3 and "slut" in choice_made.lower()):
            return StoryNode(
                node_id=f"chapter_{chapter}" if chapter > 1 else "start",
                text=f_("And there, under the big oak tree, {name} found the magic book! It shone in all the colors of the rainbow. When {name} opened it, the whole forest was filled with music and all the animals could talk again.\n\n")Tack, {name}!\" ropade alla djuren i kör. \"Du är vår hjälte!\"\n\n{name} log stort. Det hade varit det bästa äventyret någonsin, och {name} visste att det fanns många fler äventyr att upptäcka i den Förtrollade Skogen.\n\n✨ SLUT ✨",
                choices=[],
                keywords=["bok", "skog", "regnbåge", "djur", "hjälte"],
                is_ending=True,
                chapter=chapter,
            )

        story_data = stories.get(chapter, stories[1])

        node_id = f"chapter_{chapter}" if chapter > 1 else "start"
        choices = [
            StoryChoice(text=c["text"], emoji=c.get("emoji", ""), next_node_id=f"chapter_{chapter+1}_{i}")
            for i, c in enumerate(story_data["choices"])
        ]

        return StoryNode(
            node_id=node_id,
            text=story_data["text"],
            choices=choices,
            keywords=story_data["keywords"],
            is_ending=False,
            chapter=chapter,
        )

    def generate_quiz(self, story_text, num_questions=3, language="sv"):
        return [
            QuizQuestion(
                question="Vad hette ugglan i berättelsen?",
                options=["Uffe", "Olle", "Kalle"],
                correct_index=0,
                explanation="Ugglan presenterade sig som Uffe.",
            ),
            QuizQuestion(
                question="Vad hade försvunnit i skogen?",
                options=["En magisk bok", "En gyllene krona", "En trollstav"],
                correct_index=0,
                explanation="Den magiska boken hade försvunnit och utan den kunde djuren inte prata.",
            ),
            QuizQuestion(
                question="Vad hade räven runt halsen?",
                options=["Ett halsband", "En gyllene nyckel", "En sjal"],
                correct_index=1,
                explanation="Räven hade en gyllene nyckel runt halsen som öppnade vägen till bokens gömställe.",
            ),
        ]


def create_provider(provider_type: str = "demo", api_key: str = "") -> AIProvider:
    """Factory function to create an AI provider."""
    if provider_type == "openai" and api_key:
        return OpenAIProvider(api_key)
    elif provider_type == "anthropic" and api_key:
        return AnthropicProvider(api_key)
    return DemoProvider()
