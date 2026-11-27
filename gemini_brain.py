import json
import random
import re
from difflib import SequenceMatcher
from pathlib import Path

from gemini_client import generate_json
from styles import CHANNEL_NAME

CATEGORIES = [
    "Animals",
    "Landscapes",
    "Flowers & Plants",
    "Seascapes & Skies",
    "Still Life",
    "Portraits & People",
    "Buildings & Cities",
    "Techniques & Color",
]
MEDIUMS = ["acrylic", "watercolor", "oil", "gouache"]

STOP_WORDS = {"the", "a", "an", "of", "to", "how", "you", "your", "and", "in", "is", "for", "on",
              "paint", "painting", "with", "beginner", "beginners", "tutorial", "step", "easy",
              "acrylic", "watercolor", "oil", "gouache"}

REQUIRED_KEYS = ["name", "theme", "topic_angle", "audience_reason", "visual_ideas"]


def load_history():
    history_file = Path("output/decision_history.json")
    if not history_file.exists():
        return []
    try:
        history = json.loads(history_file.read_text(encoding="utf-8"))
        return history if isinstance(history, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _words(title):
    text = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    return {w for w in text.split() if w not in STOP_WORDS}


def _similar(a, b):
    if not a or not b:
        return False
    if a.strip().lower() == b.strip().lower():
        return True
    if SequenceMatcher(None, a.lower(), b.lower()).ratio() >= 0.8:
        return True
    wa, wb = _words(a), _words(b)
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= 0.6


def is_duplicate(title, past_titles):
    """Catches re-worded titles too. Words like 'paint', 'beginner', 'acrylic' are ignored,
    so 'How to Paint a Lion' and 'Lion Painting for Beginners' count as the same topic."""
    core = title.split(":")[0]
    for past in past_titles:
        if _similar(title, past) or _similar(core, past.split(":")[0]):
            return True
    return False


def validate_topic(result):
    if not isinstance(result, dict):
        return "not a JSON object"
    missing = [k for k in REQUIRED_KEYS if not result.get(k)]
    if missing:
        return f"missing keys: {missing}"
    return None


def choose_destination():
    """Pick today's painting lesson. (Function name kept so other files still work.)"""
    history = [h for h in load_history() if isinstance(h, dict) and h.get("destination")]

    recent = history[-30:]
    older = history[:-30]
    sample = random.sample(older, min(30, len(older))) if older else []
    avoid_titles = [h["destination"] for h in recent + sample]
    all_past_titles = [h["destination"] for h in history]
    recent_themes = [h["theme"] for h in history[-3:] if h.get("theme")]
    recent_mediums = [h["medium"] for h in history[-2:] if h.get("medium")]

    rejected = []
    for attempt in range(3):
        extra = ""
        if rejected:
            extra = "\nThese were rejected as duplicates, pick something clearly different:\n" \
                    + json.dumps(rejected, ensure_ascii=False)

        prompt = f"""
You are the creative director of a YouTube channel called "{CHANNEL_NAME}". We teach painting to beginners and hobby painters with clear 4-minute video lessons.

Audience: English-speaking beginner and hobby painters (United States, United Kingdom, Europe, Australia).

Your task: choose ONE painting lesson topic ("How to paint ...").

RULES:
1. ROTATE CATEGORIES. Allowed categories: {json.dumps(CATEGORIES)}.
   The most recent categories were (oldest first): {json.dumps(recent_themes)}. Do NOT use any of them again.
2. Pick a medium from {json.dumps(MEDIUMS)} that fits the subject. Recent mediums were: {json.dumps(recent_mediums)}; use a different one if it makes sense.
3. The subject must be paintable by a beginner in one session and explainable in 4 minutes (for example a lion, a sunset over the sea, a mountain lake, sunflowers, a bowl of fruit, a rainy street).
4. Do NOT choose a copy of a famous existing artwork, a cartoon character, a brand, or a style of a living artist.
5. Prefer water-based, low-risk materials (acrylic, watercolor, gouache). Oil painting is allowed, but only with a simple safe method.
6. The topic must not be similar to these past topics:
{json.dumps(avoid_titles, ensure_ascii=False)}
{extra}

Return ONLY valid JSON:
{{
  "name": "Video title idea, for example 'How to Paint a Lion in Acrylic: Easy Step-by-Step Lesson'",
  "country": "Global",
  "theme": "One of the allowed categories, written exactly",
  "medium": "acrylic, watercolor, oil or gouache",
  "topic_angle": "The specific angle of the lesson, and what the viewer will be able to paint at the end",
  "audience_reason": "Why beginners will click on this",
  "research_query": "1-3 words about the SUBJECT to look up on Wikipedia, e.g. 'Lion'",
  "visual_ideas": [
    "Close-up of hands mixing orange and brown paint on a palette",
    "A canvas with the first rough shapes of the lion's head",
    "The finished lion painting on a wooden easel"
  ]
}}
"""
        # max_tokens is high because newer Gemini models also count "thinking" tokens in it.
        result = generate_json(prompt, temperature=0.8, max_tokens=4000, validate=validate_topic)
        title = str(result["name"]).strip()

        if is_duplicate(title, all_past_titles):
            print(f"Duplicate topic, trying again: {title}", flush=True)
            rejected.append(title)
            continue

        result["name"] = title
        result.setdefault("country", "Global")
        if not isinstance(result["visual_ideas"], list):
            result["visual_ideas"] = [str(result["visual_ideas"])]
        print("Topic selected and verified unique!", flush=True)
        return result

    raise RuntimeError("Failed to generate a unique topic after 3 attempts.")


if __name__ == "__main__":
    print(json.dumps(choose_destination(), indent=4, ensure_ascii=False))
