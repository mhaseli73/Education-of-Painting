import json
from datetime import datetime, timezone
from pathlib import Path

from common import load_json, save_json
from gemini_brain import choose_destination, load_history
from styles import pick_style

AUDIENCE = "English-speaking beginner and hobby painters (US, UK, Europe, Australia)"


def main():
    """Step 1: pick a lesson topic and write output/video_plan.json (ONE long video).
    The topic is saved to history LATER, by record_history(), only after the upload worked."""
    output = Path("output")
    output.mkdir(exist_ok=True)

    print("Gemini AI is selecting today's painting lesson...")
    topic = choose_destination()
    print("Selected:", topic["name"], "|", topic.get("theme", ""), "|", topic.get("medium", ""))
    style = pick_style(load_history())
    print("Lesson format:", style)

    plans = [{
        "style": style,
        "destination": topic["name"],  # key name kept so the other files keep working
        "country": topic.get("country", "Global"),
        "theme": topic.get("theme", ""),
        "medium": topic.get("medium", ""),
        "topic_angle": topic["topic_angle"],
        "audience_reason": topic.get("audience_reason", ""),
        "research_query": topic.get("research_query", ""),
        "visual_ideas": topic.get("visual_ideas", []),
        "language": "English",
        "audience": AUDIENCE,
        "status": "planned",
        "video_type": "long",
        "duration": 240,
    }]
    save_json(output / "video_plan.json", plans)
    print("AI video plan created successfully!")
    print(json.dumps(plans, indent=4, ensure_ascii=False))


def record_history():
    """Last step of the pipeline: remember the topic so it is not used again."""
    output = Path("output")
    plan = load_json(output / "video_plan.json")[0]
    history_file = output / "decision_history.json"

    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []
    if not isinstance(history, list):
        history = []

    if any(isinstance(h, dict) and h.get("destination") == plan["destination"] for h in history):
        print("Topic already in history.")
        return

    history.append({
        "destination": plan["destination"],
        "country": plan["country"],
        "theme": plan.get("theme", ""),
        "medium": plan.get("medium", ""),
        "style": plan.get("style", ""),
        "topic_angle": plan["topic_angle"],
        "date": datetime.now(timezone.utc).isoformat(),
    })
    save_json(history_file, history)
    print("Topic saved to history.")


if __name__ == "__main__":
    main()
