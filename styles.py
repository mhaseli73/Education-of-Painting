"""Lesson formats and picture style for the painting channel.
Each day one lesson format is chosen (the last 3 are not used again), so lessons do not all
sound the same. A format changes: script structure, length, opening, lighting mood of the pictures,
title color/position, zoom and background music. The format is saved in the history."""
import os
import random

CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Easy Painting Lessons")  # change here or with a variable

STYLES = {
    "step_by_step": {
        "structure": (
            "1. HOOK: describe the finished painting and promise that a beginner can do it.\n"
            "2. MATERIALS: a short list of simple, generic materials (no brand names).\n"
            "3. FIVE STEPS in the order a painter really works. For each step say what to do, "
            "which colors to mix, how to hold or use the brush, and one common mistake to avoid.\n"
            "4. FINISH: two final tips, then a question for the audience."),
        "hook": "Open by describing the finished result and the one detail that makes it look real.",
        "words": (580, 640),
        "accent": "warm golden", "title_color": (255, 235, 0), "title_y": 0.5, "zoom": 0.08,
    },
    "beginner_mistakes": {
        "structure": (
            "Teach through 5 COMMON BEGINNER MISTAKES for this subject. For each mistake: what it "
            "looks like, why it happens, and the simple fix. Finish with the one habit that improves "
            "everything, and a question for the audience."),
        "hook": "Open with: 'Almost every beginner makes this mistake when painting this.'",
        "words": (540, 600),
        "accent": "soft natural", "title_color": (255, 150, 120), "title_y": 0.5, "zoom": 0.06,
    },
    "materials_first": {
        "structure": (
            "1. Start with a cheap STARTER SET: what you need and why (generic names only).\n"
            "2. SET UP: how to arrange the table, light and water or palette.\n"
            "3. FOUR PAINTING STAGES: background, main shapes, details, final touches.\n"
            "4. End with a tip for practice and a question for the audience."),
        "hook": "Open with: 'You do not need expensive supplies to paint this.'",
        "words": (560, 620),
        "accent": "bright sunny", "title_color": (150, 255, 150), "title_y": 0.8, "zoom": 0.10,
    },
    "color_focus": {
        "structure": (
            "Build the lesson around COLOR. Explain the 4 to 6 colors needed, how to mix each one, "
            "how to show light and shadow, and then give a short overview of the painting steps. "
            "Finish with a color tip to remember and a question for the audience."),
        "hook": "Open with a surprising color fact about this subject, for example which colors make it look real.",
        "words": (560, 620),
        "accent": "cool blue", "title_color": (120, 220, 255), "title_y": 0.5, "zoom": 0.07,
    },
    "one_technique": {
        "structure": (
            "Teach ONE technique (for example blending, layering, dry brush or glazing) and use it "
            "to paint this subject in 3 clear stages. Explain what the technique is, why it works, "
            "and how to practice it. Finish with a quick practice exercise and a question for the audience."),
        "hook": "Open by naming the technique and what it will let the viewer do.",
        "words": (520, 580),
        "accent": "calm muted", "title_color": (230, 160, 255), "title_y": 0.8, "zoom": 0.09,
    },
    "question_answer": {
        "structure": (
            "Write it as a conversation: a curious beginner asks 4 short questions about painting this "
            "subject and you answer each one clearly in simple words. Use real questions beginners ask. "
            "Finish with the most important idea and a question for the audience."),
        "hook": "Open with the question beginners ask most about painting this subject.",
        "words": (520, 580),
        "accent": "moody dramatic", "title_color": (100, 255, 230), "title_y": 0.5, "zoom": 0.12,
    },
}


def pick_style(history):
    """Choose a format that was not used in the last 3 videos."""
    recent = [h.get("style") for h in history[-3:] if isinstance(h, dict)]
    choices = [s for s in STYLES if s not in recent] or list(STYLES)
    return random.choice(choices)


def get_style(style_id):
    return STYLES.get(style_id) or STYLES["step_by_step"]


# ---------------------------------------------------------------------------------------------
# PICTURE STYLE. Default is "realistic". Set the env var IMAGE_STYLE=illustration for a drawn look.
# ---------------------------------------------------------------------------------------------
VISUALS = {
    "realistic": {
        "name": "realistic",
        "prefix": ("Ultra realistic high quality photograph, {accent} light, shallow depth of field, "
                   "cozy art studio, close-up on hands and canvas, no faces, "
                   "no text, no letters, no logos, showing: "),
        "scene_rules": ("REALISTIC PHOTOGRAPHS of a painting being made: close-ups of hands holding brushes, "
                        "the canvas at different stages, paint palettes with the mixed colors, brush strokes, "
                        "art supplies on a wooden table, and the finished painting on an easel. "
                        "Show hands, canvas and tools. Do not show people's faces"),
        "fallback": "A realistic photo of hands painting on a canvas in an art studio. Scene about: ",
    },
    "illustration": {
        "name": "illustration",
        "prefix": ("Soft watercolor style illustration, {accent} colors, art studio, "
                   "no text, no letters, no logos, showing: "),
        "scene_rules": ("soft illustrations of a painting being made: hands with brushes, canvas, "
                        "paint palettes, art supplies, the finished painting. Do not show faces"),
        "fallback": "An illustration of a brush painting on a canvas. Scene about: ",
    },
}


def visual():
    return VISUALS.get(os.getenv("IMAGE_STYLE", "realistic").lower(), VISUALS["realistic"])


def image_prefix(accent):
    return visual()["prefix"].format(accent=accent)
