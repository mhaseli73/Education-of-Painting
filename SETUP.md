# Setup for the NEW painting channel (new GitHub repository)

1. Create a new GitHub repository (private or public) and upload all files of this project.
   Check that the hidden folder `.github/workflows/daily.yml` was uploaded.
2. Add GitHub secrets (Settings -> Secrets and variables -> Actions):
   - `GEMINI_API_KEY` (you can use the same key as your other project)
   - `YT_TOKEN_JSON` -> a NEW token for the PAINTING channel (see step 3)
3. Make the YouTube token for the painting channel:
   - Use the same `client_secrets.json` as before (same Google Cloud project, OAuth app "In production").
   - Run `python get_youtube_token.py` on your computer. When Google asks which account or channel to use,
     choose the PAINTING channel. A token belongs to ONE channel. If you pick the wrong one, the videos go to the wrong channel.
   - Paste the whole content of `token.json` into the secret `YT_TOKEN_JSON`.
4. Add music (optional but nice): put your own free-to-use tracks in `output/` named `bgm.mp3`, `bgm_2.mp3`, ...
   Without music the videos are made without background music.
5. Settings -> Actions -> General -> Workflow permissions -> "Read and write permissions" (to save the history).
6. Run the workflow by hand (Actions -> Run workflow). Keep videos `private` for the first runs and check them.
   Set `YT_PRIVACY_STATUS: public` in the workflow when you are happy.
7. Never upload `token.json` or `client_secrets.json`.
