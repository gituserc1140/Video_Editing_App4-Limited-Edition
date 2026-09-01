# JSON2Video Video Editing Micro-App

A Streamlit micro-app for simple video editing powered by the [json2video.com](https://json2video.com/) API.

## Repository structure

- `app.py` — Streamlit entrypoint
- `api_client.py` — JSON2Video API client (`fetch_data()` uploads, renders, polls)
- `ui/` — Streamlit UI form and result rendering
- `static/` — app styling assets
- `config/` — environment-configurable settings
- `README.md` — usage instructions

## Requirements

- Python 3.10+
- A [json2video.com](https://json2video.com/) API key

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

## How to use

1. **Enter API key**
   - Paste your JSON2Video API key into the `JSON2Video API key` field.

2. **Choose item counts**
   - Above the form, pick `Number of video clips` (1-5), `Text overlays` (0-5), `Image/watermark overlays` (0-5), and `Audio tracks` (0-3). The form below adjusts to show that many sets of controls.

3. **Configure edits**
   - **Video Quality**: choose `Resolution` (sd/hd/full-hd) and `Quality` (low/medium/high).
   - **Visual Adjustments** (applied to every clip): `Playback speed`, `Rotation`, an optional Ken Burns-style `zoom` effect, `Brightness`/`Contrast`/`Saturation` sliders, a `Color preset` (grayscale/sepia), and optional audio ducking (`Duck video audio under music/narration`) that lowers each clip's own audio while other tracks play.
   - **Transition between clips**: when more than one clip is used, choose a `Transition type` (fade/wipe/slide/zoom) and duration applied between scenes.
   - **Clips**: for each clip, upload an MP4/MOV/WEBM/M4V file and set `Trim start`/`Trim end`, `Original video volume`/`Mute`, and `Video fade-in`/`Video fade-out`.
   - **Text Styling**: for each text overlay, set the text, a `Start offset`/`Duration` (so overlays can appear at specific times instead of spanning the whole clip), `Font family`, `Font size`, `Text color`, optional `Text background color`, vertical/horizontal position, and a `Text style preset`.
   - **Audio**: for each audio track (background music or narration), set a publicly accessible audio URL, `Volume`, `Fade-in`/`Fade-out`, and `Start offset`.
   - **Watermark / Logo overlays**: for each image overlay, upload an image with configurable `Position`, `Opacity`, `Start offset`, and `Duration` (0 = spans the whole video).
   - **AI Voiceover**: enable `Add AI voiceover narration`, enter a `Narration script`, and choose a `Voice` and `Voice model` (azure/elevenlabs) to generate spoken narration for the movie.
   - **Auto Captions / Subtitles**: enable `Add automatic captions` to transcribe the movie's audio (including AI voiceover) into on-screen captions, with configurable `Caption language`, `Transcription model` (default/whisper), `Caption style`, `Caption font size`, and `Caption position`.

4. **Render video**
   - Click `Render Video`.
   - The app uploads each source file via `POST /v2/media/file` (which returns a pre-signed upload URL), submits a JSON2Video movie via `POST /v2/movies`, polls render status with `GET /v2/movies?project={project_id}`, then displays the final video.

5. **Download output**
   - Use the `Download rendered video` link shown after render completion.

## Notes

- Trim end must be greater than trim start for every clip.
- The app keeps API key entry in the UI (not hard-coded).
- Text overlays are only added to the first clip's scene; subsequent clips render without overlays layered on top (a scope limitation for multi-clip renders).
- Audio tracks and image/watermark overlays are added as movie-wide elements, so they span across all clips/scenes rather than a single clip.
- The JSON2Video free tier does not restrict which element types, filters, or transitions are available — it limits total render credits, maximum video length (~3 minutes), and always adds a watermark. None of the controls in this app require a paid plan.
- AI voiceover and auto-captions rely on JSON2Video's built-in TTS/transcription providers (Azure/ElevenLabs, Whisper) and may consume render credits faster than plain video edits since they add processing time.
- Polling and timeout behavior can be adjusted via environment variables in `config/settings.py`.
- Deployment (e.g. to Streamlit Community Cloud) is done manually and is outside the scope of this repository.
