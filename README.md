# Painting-video-automation

AI-automated painting lesson channel. Every day it picks a lesson ("How to paint a lion in acrylic"),
writes a checked script, makes realistic pictures, a voiceover and a 3-4 minute video with a thumbnail,
and uploads it to YouTube. Long videos only (no Shorts).

## Pipeline (`python pipeline.py`)
1. `main.py` - Gemini picks a lesson (categories and mediums rotate, duplicates are blocked) and a lesson format
2. `researcher.py` - short Wikipedia background about the subject
3. `script_generator.py` + `script_checker.py` - script, then an automatic accuracy / safety / logic check
4. `scene_planner.py` - splits the script into 24 scenes, Gemini adds a picture idea per scene
5. `visual_fetcher.py` - realistic pictures (Pollinations)
6. `voiceover_generator.py` - edge-tts voice
7. `video_renderer.py` - pictures + voice + music -> mp4
8. `thumbnail_generator.py` - JPEG thumbnail
9. `youtube_uploader.py` - upload (marked "contains AI-generated realistic content")
10. the lesson is saved to `output/decision_history.json` (only after a successful upload)

If a run fails, running it again continues from the failed step (`output/run_state.json`, valid 12 hours).

## Secrets / settings
See SETUP.md. Secrets: `GEMINI_API_KEY`, `YT_TOKEN_JSON`.
Optional variables: `YT_PRIVACY_STATUS`, `CHANNEL_NAME`, `IMAGE_STYLE`, `YT_AI_DISCLOSURE`, `TTS_VOICE`,
`GEMINI_PRIMARY_MODEL`, `GEMINI_FALLBACK_MODEL`, `IMAGE_DELAY_SECONDS`, `SCRIPT_CHECK_STRICT`.
