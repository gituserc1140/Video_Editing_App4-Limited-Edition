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
   - Add `Text overlay` (optional).
   - Add an `Optional music URL` (optional, must be a publicly accessible audio URL).

4. **Render video**
   - Click `Render Video`.
   - The app uploads your source file via `POST /v2/media/file` (which returns a pre-signed upload URL), submits a JSON2Video movie via `POST /v2/movies`, polls render status with `GET /v2/movies?project={project_id}`, then displays the final video.

5. **Download output**
   - Use the `Download rendered video` link shown after render completion.

## Notes

- Trim end must be greater than trim start.
- The app keeps API key entry in the UI (not hard-coded).
- Polling and timeout behavior can be adjusted via environment variables in `config/settings.py`.
- Deployment (e.g. to Streamlit Community Cloud) is done manually and is outside the scope of this repository.
