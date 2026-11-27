from pathlib import Path

import script_checker
from common import clean_for_speech, load_json, save_json
from gemini_client import generate_json
from styles import get_style

# Voice speed is about 2.5 words per second, so 4 minutes is ~600 words.
# The real target comes from the daily lesson format; these are only the allowed limits.

SPEECH_RULES = (
    "The narration is read by a text-to-speech voice. Write plain spoken sentences only: "
    "no headings, no bullet points, no markdown, no emojis, no hashtags, no stage directions "
    "or notes in brackets. Do not name real brands, living artists or famous artworks. "
    "Speak to the viewer as 'you'."
)


def make_validator(style):
    low, high = style["words"][0] - 100, style["words"][1] + 200

    def validate(result):
        if not isinstance(result, dict):
            return "not a JSON object"
        if not str(result.get("title", "")).strip():
            return "missing title"
        words = len(str(result.get("narration", "")).split())
        if not low <= words <= high:
            return f"narration has {words} words, expected {low}-{high}"
        return None

    return validate


def build_prompt(plan, research, style):
    return f"""
You are a skilled painting teacher and YouTube scriptwriter. You write a clear voice-over for a 4-minute beginner painting lesson.

LESSON: {plan['destination']}
CATEGORY: {plan.get('theme', '')}
MEDIUM: {plan.get('medium', '')}
ANGLE: {plan.get('topic_angle', '')}
WHY VIEWERS CLICK: {plan.get('audience_reason', '')}
BACKGROUND ABOUT THE SUBJECT (Wikipedia, may be empty): {research.get('description', '')}

TARGET LENGTH: {style['words'][0]} to {style['words'][1]} words.

CRITICAL RULES:
1. Teach REAL, correct technique for the chosen medium. Use generic material names (for example "a flat brush", "ultramarine blue", "burnt sienna"), never brand names.
   Correct basics: watercolor goes from light to dark and keeps the white of the paper; acrylic dries fast and dries slightly darker; oil paint is built "fat over lean" and needs good ventilation if solvents are used.
2. Give concrete details: which colors to mix, how much water or paint, which brush, which part to paint first and why.
3. Add ONE short safety tip about the materials where it fits (ventilation for solvents, washing hands, never put brushes in your mouth, do not pour paint water or solvents down the drain).
4. Do not invent facts, statistics or art history. Facts about the subject must be general and well known.
5. The pictures in the video are illustrations, not a recording of you painting. NEVER say "watch me", "as I paint", "my painting" or "as you can see me do". Guide the viewer: "Now you mix...", "Next, load your brush...".
6. {SPEECH_RULES}

LESSON FORMAT (follow this structure):
{style['structure']}
OPENING: {style['hook']}
The video must end with a natural question for the audience, for example "What would you like to paint next? Tell me in the comments!"

Return ONLY valid JSON:
{{
  "title": "SEO video title, maximum 90 characters, no hashtags",
  "hook": "Opening hook",
  "narration": "Complete voice-over script",
  "visual_suggestions": ["Visual 1", "Visual 2"],
  "description": "YouTube description, 2-3 short paragraphs with a materials list, no < or > characters",
  "tags": ["8 to 12 short tags, for example painting, acrylic painting, how to paint"]
}}
"""


def main():
    output = Path("output")
    script_folder = output / "scripts"
    script_folder.mkdir(parents=True, exist_ok=True)

    plans = load_json(output / "video_plan.json")
    research = load_json(output / "destination_research.json")

    for plan in plans:
        video_type = plan["video_type"]  # always "long" in this project
        print(f"Generating {video_type} script...", flush=True)
        style = get_style(plan.get("style"))

        result = generate_json(build_prompt(plan, research, style), temperature=0.7, max_tokens=8000,
                               validate=make_validator(style))

        result["narration"] = clean_for_speech(result["narration"])
        result["title"] = " ".join(str(result["title"]).split())
        if not isinstance(result.get("tags"), list):
            result["tags"] = []

        # Automatic accuracy/safety/logic check. Fixes the script or stops the run (see script_checker.py).
        result = script_checker.check_and_fix(result, plan, research.get("description", ""), style, video_type)

        result["destination"] = plan["destination"]
        result["country"] = plan["country"]

        filename = script_folder / f"{video_type}_script.json"
        save_json(filename, result)
        print(f"Created: {filename} ({len(result['narration'].split())} words)", flush=True)


if __name__ == "__main__":
    main()
