"""Automatic check of every painting script Gemini writes, BEFORE any image, voice or upload is made.

Two layers:
  1. RULES (plain Python, fast, always the same): brand / artist names, risky or unsafe claims,
     numbers that look invented, "watch me paint" lines (the pictures are AI illustrations),
     repeated sentences, very long sentences, wrong ending.
  2. AI EDITOR (a second Gemini call with a strict reviewer prompt): technique accuracy for the medium,
     order of the steps, material safety, invented facts, honesty, clarity.

If there are blocking problems, Gemini is asked to rewrite the script to fix them (max 2 rounds).
If it still fails, the step stops with an error. The workflow then retries, which writes a NEW
script, and nothing is uploaded. Set SCRIPT_CHECK_STRICT=0 to only warn and continue.
The result is saved in output/scripts/<type>_check.json so you can read what was found.
"""
import os
import re
from pathlib import Path

from common import clean_for_speech, save_json
from gemini_client import generate_json

MAX_REVISIONS = 2
STRICT = os.getenv("SCRIPT_CHECK_STRICT", "1") != "0"

BRANDS = [
    "winsor and newton", "winsor & newton", "liquitex", "golden acrylics", "daler rowney",
    "daler-rowney", "arteza", "faber-castell", "holbein", "sennelier", "amazon", "etsy", "walmart",
    "michaels", "hobby lobby", "bob ross", "van gogh", "picasso", "monet", "da vinci",
    "leonardo", "rembrandt", "mona lisa", "starry night", "banksy", "disney",
]
# Unsafe or over-promising statements. Add more patterns here when you see new problems.
RISKY_CLAIMS = [
    r"guarantee[sd]?", r"perfect every time", r"always works", r"never fails",
    r"no need (?:for|to) (?:ventilat\w*|wear|wash)",
    r"safe to (?:eat|drink|taste|swallow)",
    r"completely (?:safe|non-?toxic)",
    r"(?:pour|dump|tip) (?:it |them )?(?:down|into) the (?:drain|sink)",
]
# The pictures are AI illustrations, so the narrator must not pretend to be painting live.
FAKE_LIVE = [
    r"\bwatch me\b", r"\bas i paint\b", r"\bi'?m painting\b", r"\bi am painting\b",
    r"\bmy painting\b", r"\bi painted\b", r"\bhere i am\b", r"\bas you can see me\b",
    r"\bmy hands?\b", r"\bmy brush\b", r"\bmy palette\b",
]
STAT_PATTERNS = (
    r"\b(?:million|billion)\b",
    r"\bstudies (?:show|say|found)\b", r"\bresearch (?:shows|says|found)\b",
    r"\bexperts (?:say|agree)\b", r"\baccording to\b", r"\bsurveys? (?:show|found)\b",
)


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _issue(severity, quote, problem, source="rule"):
    return {"severity": severity, "quote": quote[:200], "problem": problem, "source": source}


def rule_issues(narration, video_type, research_text=""):
    issues = []
    sentences = split_sentences(narration)
    research_lower = (research_text or "").lower()
    seen = set()

    for sentence in sentences:
        low = sentence.lower()

        for brand in BRANDS:
            if re.search(rf"\b{re.escape(brand)}\b", low):
                issues.append(_issue("error", sentence, f"Names a real brand, artist or artwork ('{brand}'). Use a general word instead."))
                break

        for pattern in RISKY_CLAIMS:
            if re.search(pattern, low):
                issues.append(_issue("error", sentence, "Unsafe or over-promising statement. Make it safe and general."))
                break

        for pattern in FAKE_LIVE:
            if re.search(pattern, low):
                issues.append(_issue("error", sentence,
                                     "Speaks as if the narrator is painting live. The pictures are illustrations: guide the viewer with 'you' instead."))
                break

        # Statistics and "studies show" claims: allowed only when the number is in the research text.
        # (Mixing ratios like "50 percent water" are fine and are not checked.)
        if any(re.search(p, low) for p in STAT_PATTERNS):
            numbers = [n.strip(",.") for n in re.findall(r"\d[\d,\.]*", sentence)]
            if not numbers or not all(n in research_lower for n in numbers):
                issues.append(_issue("error", sentence,
                                     "Looks like an unsupported statistic or claim. Remove it or say it in a general way."))

        normalized = re.sub(r"[^a-z0-9 ]", "", low)
        if len(normalized.split()) >= 5 and normalized in seen:
            issues.append(_issue("error", sentence, "Repeated sentence."))
        seen.add(normalized)

        if len(sentence.split()) > 40:
            issues.append(_issue("warning", sentence, "Very long sentence. Hard to listen to."))

    ending = (sentences[-1] if sentences else "").lower()
    if "?" not in ending and "comment" not in " ".join(sentences[-2:]).lower():
        issues.append(_issue("warning", sentences[-1] if sentences else "",
                             "The video should end with a question for the audience."))
    return issues


def ai_review(script, plan, research_text, style):
    """Second Gemini call. Low temperature, strict editor, no creative writing."""
    prompt = f"""
You are a strict editor and technical checker for a YouTube channel that teaches painting to beginners.
Check the script below. You are NOT a writer: do not rewrite it, only find real problems.

LESSON: {plan['destination']}
MEDIUM: {plan.get('medium', '')}
TITLE: {script['title']}
EXPECTED FORMAT: {style['structure']}
BACKGROUND (Wikipedia, may be empty): {research_text}

SCRIPT TO CHECK:
\"\"\"{script['narration']}\"\"\"

CHECK THESE POINTS:
1. TECHNIQUE: Are the painting techniques, color mixes, brush use and material use correct for the medium?
   (Examples: yellow + blue makes green; watercolor goes light to dark and keeps the paper white; acrylic dries fast
   and dries slightly darker; oil is built fat over lean.) Wrong or misleading technique is an error.
2. ORDER: Are the steps in a sensible order that a real painter would follow? Can each step be done after the previous one?
3. SAFETY: Is there any unsafe advice about solvents, ventilation, toxic pigments, brush cleaning, waste, or children?
   Unsafe advice is an error. Solvent use without a ventilation hint is an error.
4. FACTS: Any invented statistic, art history, or wrong fact about the subject (for example animal facts) is an error.
5. HONESTY: The pictures are AI illustrations. The script must not say or imply that the narrator is painting live.
6. FIT AND CLARITY: Does it match the title and the expected format? Is anything confusing for a beginner?

Mark severity "error" only for REAL problems (wrong, unsafe, illogical, unsupported). Use "warning" for small improvements.
Do not invent problems. If the script is fine, return verdict "pass" and an empty list.

Return ONLY valid JSON:
{{
  "verdict": "pass or fail",
  "issues": [
    {{"severity": "error or warning", "quote": "short exact quote from the script", "problem": "what is wrong", "fix": "how to fix it"}}
  ]
}}
"""

    def validate(result):
        if not isinstance(result, dict) or result.get("verdict") not in ("pass", "fail"):
            return "bad verdict"
        if not isinstance(result.get("issues", []), list):
            return "issues is not a list"
        return None

    result = generate_json(prompt, temperature=0.2, max_tokens=8000, validate=validate)
    issues = []
    for item in result.get("issues", []):
        if isinstance(item, dict):
            problem = str(item.get("problem", "")) + (f" Fix: {item['fix']}" if item.get("fix") else "")
            severity = item.get("severity") if item.get("severity") in ("error", "warning") else "warning"
            issues.append(_issue(severity, str(item.get("quote", "")), problem, source="ai"))
    return issues


def revise(script, issues, style, video_type):
    """Ask Gemini to fix ONLY the listed problems and keep everything else."""
    words = len(script["narration"].split())
    problems = "\n".join(f"- [{i['severity']}] \"{i['quote']}\" -> {i['problem']}" for i in issues)

    prompt = f"""
You are editing a voice-over script for a beginner painting lesson video.
Rewrite the narration so that ALL problems below are fixed. Keep everything that is not a problem.

PROBLEMS:
{problems}

RULES:
- Keep the same lesson format and about the same length ({int(words * 0.9)} to {int(words * 1.1)} words).
- Teach correct technique for the medium. Use generic material names only: no brands, living artists or famous artworks.
- The pictures are AI illustrations: never say "watch me", "as I paint" or "my painting". Speak to the viewer as "you".
- Keep one short material-safety tip where it fits.
- Plain spoken sentences only: no markdown, emojis, hashtags or notes in brackets.
- The script must still end with a question for the audience.

CURRENT NARRATION:
\"\"\"{script['narration']}\"\"\"

Return ONLY valid JSON: {{"narration": "the corrected full narration"}}
"""
    low, high = int(words * 0.65), int(words * 1.35)

    def validate(result):
        text = result.get("narration") if isinstance(result, dict) else None
        if not isinstance(text, str) or not low <= len(text.split()) <= high:
            return f"narration missing or not between {low} and {high} words"
        return None

    return generate_json(prompt, temperature=0.4, max_tokens=8000, validate=validate)["narration"]


def check_and_fix(script, plan, research_text, style, video_type="long", long_narration="",
                  output_dir=Path("output")):
    """Return the (possibly corrected) script. Raises RuntimeError when it cannot be fixed (strict mode)."""
    history = []
    for round_number in range(MAX_REVISIONS + 1):
        print(f"  Script check ({video_type}), round {round_number + 1}...", flush=True)
        issues = rule_issues(script["narration"], video_type, research_text)
        try:
            issues += ai_review(script, plan, research_text, style)
        except RuntimeError as error:
            # The reviewer itself is down. Rules still ran. Do not block a good script for this.
            print(f"  AI reviewer not available ({error}). Using rule checks only.", flush=True)

        errors = [i for i in issues if i["severity"] == "error"]
        history.append({"round": round_number + 1, "errors": len(errors), "issues": issues})
        print(f"  -> {len(errors)} error(s), {len(issues) - len(errors)} warning(s)", flush=True)
        for item in errors:
            print(f"     ERROR: \"{item['quote'][:80]}\" -> {item['problem'][:120]}", flush=True)

        if not errors:
            _save_report(output_dir, video_type, "passed", history)
            return script

        if round_number == MAX_REVISIONS:
            break
        script["narration"] = clean_for_speech(revise(script, errors, style, video_type))

    _save_report(output_dir, video_type, "failed", history)
    if STRICT:
        raise RuntimeError(f"The {video_type} script did not pass the check after {MAX_REVISIONS} revisions. "
                           f"See output/scripts/{video_type}_check.json")
    print("  WARNING: script still has errors, but SCRIPT_CHECK_STRICT=0 so the run continues.", flush=True)
    return script


def _save_report(output_dir, video_type, status, history):
    folder = Path(output_dir) / "scripts"
    folder.mkdir(parents=True, exist_ok=True)
    save_json(folder / f"{video_type}_check.json", {"status": status, "rounds": history})
