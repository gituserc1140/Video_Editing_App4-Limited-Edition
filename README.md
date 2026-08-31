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

2. **Upload a video**
   - Upload an MP4/MOV/WEBM/M4V source file.

3. **Configure edits**
   - Set `Trim start (seconds)` and `Trim end (seconds)`.
   - **Video Quality**: choose `Resolution` (sd/hd/full-hd) and `Quality` (low/medium/high), adjust the original video `volume` or `Mute original video audio`, and set optional `Video fade-in`/`Video fade-out` durations.
   - **Text Styling**: add a `Text overlay` (optional) with `Font family`, `Font size`, `Text color`, optional `Text background color`, vertical/horizontal position, and a `Text style preset`.
   - **Audio**: add an `Optional music URL` (optional, must be a publicly accessible audio URL) with `Music volume`, `Music fade-in`/`Music fade-out`, and `Music start offset`.
   - **Watermark / Logo**: upload an optional watermark image with configurable `Watermark position` and `Watermark opacity`.

4. **Render video**
   - Click `Render Video`.
   - The app uploads your source file via `POST /v2/media/file` (which returns a pre-signed upload URL), submits a JSON2Video movie via `POST /v2/movies`, polls render status with `GET /v2/movies?project={project_id}`, then displays the final video.

5. **Download output**
   - Use the `Download rendered video` link shown after render completion.

## Notes

- Trim end must be greater than trim start.
- The app keeps API key entry in the UI (not hard-coded).
- All new editing controls default to the app's previous fixed behavior (sd resolution, medium quality, minimal bottom-center text style, 0.4 music volume with 1s fades) so existing workflows are unaffected unless a control is changed.
- Multiple video clips/scenes (concatenation) are not yet supported; each render uses a single uploaded clip.
- Polling and timeout behavior can be adjusted via environment variables in `config/settings.py`.
- Deployment (e.g. to Streamlit Community Cloud) is done manually and is outside the scope of this repository.
