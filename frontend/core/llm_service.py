"""
LLM Service Interface for AI Caption & Copywriting Generation.
Combines Gemini LLM generation with fallback generative options.
"""
from core.caption_generator import (
    generate_ai_captions,
    CaptionSuggestion,
    MissingAPIKeyError,
    APIFailureError,
    EmptyResponseError
)


def get_offline_captions(topic: str, audience: str, tone: str, event_type: str) -> list[CaptionSuggestion]:
    """Provides 5 structured fallback captions when offline or without an API key."""
    t = topic.strip() if topic else "Coding without coffee"
    return [
        {
            "title": "Expectation vs Reality",
            "top_text": f"WHEN YOU TRY TO {t.upper()}",
            "bottom_text": "AND EVERYTHING BREAKS ON FIRST TRY",
            "subtitle": f"The ultimate test of patience: {t}",
            "caption": f"An exclusive deep dive into how {t} actually works under the hood.",
            "badge": "RELATABLE",
            "full_caption": f"When you try to {t} and reality hits hard! 💀 #DevHumor #{t.replace(' ', '')}"
        },
        {
            "title": "Overconfident Pro",
            "top_text": f"ME EXPLAINING {t.upper()}",
            "bottom_text": "AFTER 5 MINUTES OF READING DOCUMENTATION",
            "subtitle": f"Master the art of {t} with ease",
            "caption": f"Join our comprehensive walkthrough designed specifically for {audience}.",
            "badge": "PRO TIP",
            "full_caption": f"Expert mode activated after one quick video. #Overconfidence #{t.replace(' ', '')}"
        },
        {
            "title": "Late Night Thoughts",
            "top_text": "NOBODY:\nABSOLUTELY NO ONE:",
            "bottom_text": f"ME AT 3 AM THINKING ABOUT {t.upper()}",
            "subtitle": f"Why {t} is keeping everyone awake",
            "caption": f"Discover what makes {t} the most talked-about topic in the industry.",
            "badge": "VIRAL",
            "full_caption": f"Sleep? Never heard of her. {t} on my mind 24/7. #Insomnia #{t.replace(' ', '')}"
        },
        {
            "title": "The Breakthrough",
            "top_text": f"FINALLY FIXED {t.upper()}",
            "bottom_text": "DISCOVERED 47 NEW UNKNOWN BUGS",
            "subtitle": f"The journey through {t} and beyond",
            "caption": f"A special {event_type} gathering creators, builders, and enthusiasts.",
            "badge": "EXCLUSIVE",
            "full_caption": f"One step forward, forty-seven bugs backward. #ProgrammingLife #{t.replace(' ', '')}"
        },
        {
            "title": "The Hype Train",
            "top_text": f"EVERYONE ON THEIR WAY TO {t.upper()}",
            "bottom_text": "NO TURNING BACK NOW",
            "subtitle": f"Don't miss the biggest {event_type} of the year",
            "caption": f"Register now to secure your pass for the ultimate {t} session.",
            "badge": "HYPE",
            "full_caption": f"The hype is real for {t}! See you all there! 🚀 #LiveEvent #{t.replace(' ', '')}"
        }
    ]


def generate_captions_flexible(
    topic: str,
    audience: str = "General Audience",
    tone: str = "Sarcastic & Witty",
    event_type: str = "Meme",
    api_key: str | None = None,
    timeout: int = 20
) -> tuple[list[CaptionSuggestion], str | None]:
    """
    Attempts to generate 5 captions via LLM API.
    If an error occurs or no key is present, returns 5 fallback suggestions along with an info/warning message.
    """
    try:
        results = generate_ai_captions(
            topic=topic,
            audience=audience,
            tone=tone,
            event_type=event_type,
            api_key=api_key,
            timeout=timeout
        )
        return results, None
    except MissingAPIKeyError as e:
        return get_offline_captions(topic, audience, tone, event_type), f"ℹ️ {str(e)} (Using smart offline templates)"
    except (APIFailureError, EmptyResponseError) as e:
        return get_offline_captions(topic, audience, tone, event_type), f"⚠️ {str(e)} (Switched to smart offline fallback)"
