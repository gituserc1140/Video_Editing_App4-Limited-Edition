from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st


FONT_FAMILIES = ["Default", "Roboto", "Open Sans", "Montserrat", "Oswald", "Poppins", "Lato"]
TEXT_STYLES = ["minimal", "classic", "elegant", "bold", "subtitle"]
VERTICAL_POSITIONS = ["top", "center", "bottom"]
HORIZONTAL_POSITIONS = ["left", "center", "right"]
RESOLUTIONS = ["sd", "hd", "full-hd"]
QUALITIES = ["low", "medium", "high"]
WATERMARK_POSITIONS = [
    "top-left",
    "top-center",
    "top-right",
    "center-left",
    "center-center",
    "center-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
]
ROTATIONS = [0, 90, 180, 270]
COLOR_PRESETS = ["none", "grayscale", "sepia"]
TRANSITIONS = ["none", "fade", "wipe", "slide", "zoom"]
MAX_CLIPS = 5
MAX_TEXT_OVERLAYS = 5
MAX_IMAGE_OVERLAYS = 5
MAX_AUDIO_TRACKS = 3
VOICES = [
    "en-US-EmmaMultilingualNeural",
    "en-US-AndrewMultilingualNeural",
    "en-GB-SoniaNeural",
    "es-ES-ElviraNeural",
    "fr-FR-DeniseNeural",
    "de-DE-KatjaNeural",
]
VOICE_MODELS = ["azure", "elevenlabs"]
SUBTITLE_LANGUAGES = ["auto", "en", "es", "fr", "de", "pt", "it"]
SUBTITLE_MODELS = ["default", "whisper"]
SUBTITLE_STYLES = ["classic", "classic-progressive", "bold", "minimal"]


def render_editor_form() -> Dict[str, Any]:
    st.title("JSON2Video Video Editor")
    st.caption("Upload a video, set simple edits, and render using your JSON2Video API key.")

    # Item counts are chosen outside the form so the form widget layout can react to them
    # before submission (Streamlit forms don't rerun until submitted).
    st.subheader("Clips")
    num_clips = st.number_input(
        "Number of video clips", min_value=1, max_value=MAX_CLIPS, value=1, step=1
    )
    st.subheader("Overlays")
    col_texts, col_images, col_audio = st.columns(3)
    with col_texts:
        num_text_overlays = st.number_input(
            "Text overlays", min_value=0, max_value=MAX_TEXT_OVERLAYS, value=1, step=1
        )
    with col_images:
        num_image_overlays = st.number_input(
            "Image/watermark overlays", min_value=0, max_value=MAX_IMAGE_OVERLAYS, value=0, step=1
        )
    with col_audio:
        num_audio_tracks = st.number_input(
            "Audio tracks", min_value=0, max_value=MAX_AUDIO_TRACKS, value=0, step=1
        )

    with st.form("video-editor-form"):
        api_key = st.text_input("JSON2Video API key", type="password")

        st.subheader("Video Quality")
        col_res, col_qual = st.columns(2)
        with col_res:
            resolution = st.selectbox("Resolution", RESOLUTIONS, index=0)
        with col_qual:
            quality = st.selectbox("Quality", QUALITIES, index=1)

        st.subheader("Visual Adjustments")
        st.caption("Applied to every video clip.")
        col_speed, col_rotate = st.columns(2)
        with col_speed:
            speed = st.slider("Playback speed", min_value=0.25, max_value=4.0, value=1.0, step=0.05)
        with col_rotate:
            rotate = st.selectbox("Rotation (degrees)", ROTATIONS, index=0)
        zoom_enabled = st.checkbox("Enable Ken Burns zoom effect", value=False)
        zoom_level = st.slider(
            "Zoom level", min_value=1.0, max_value=2.0, value=1.2, step=0.05, disabled=not zoom_enabled
        )
        col_bright, col_contrast, col_sat = st.columns(3)
        with col_bright:
            brightness = st.slider("Brightness", min_value=0.0, max_value=2.0, value=1.0, step=0.05)
        with col_contrast:
            contrast = st.slider("Contrast", min_value=0.0, max_value=2.0, value=1.0, step=0.05)
        with col_sat:
            saturation = st.slider("Saturation", min_value=0.0, max_value=2.0, value=1.0, step=0.05)
        color_preset = st.selectbox("Color preset", COLOR_PRESETS, index=0)
        duck_enabled = st.checkbox("Duck video audio under music/narration", value=False)
        duck_level = st.slider(
            "Duck level (lower = quieter video audio)",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            disabled=not duck_enabled,
        )

        if num_clips > 1:
            st.subheader("Transition between clips")
            col_ttype, col_tdur = st.columns(2)
            with col_ttype:
                transition_type = st.selectbox("Transition type", TRANSITIONS, index=0)
            with col_tdur:
                transition_duration = st.number_input(
                    "Transition duration (seconds)", min_value=0.1, value=1.0, step=0.1
                )
        else:
            transition_type = "none"
            transition_duration = 1.0

        st.subheader("Clips")
        clips: List[Dict[str, Any]] = []
        for i in range(int(num_clips)):
            st.markdown(f"**Clip {i + 1}**")
            video_file = st.file_uploader(
                f"Upload video for clip {i + 1}",
                type=["mp4", "mov", "webm", "m4v"],
                key=f"clip_file_{i}",
            )
            col_start, col_end = st.columns(2)
            with col_start:
                trim_start = st.number_input(
                    f"Trim start (seconds) - clip {i + 1}", min_value=0.0, value=0.0, step=0.1, key=f"trim_start_{i}"
                )
            with col_end:
                trim_end = st.number_input(
                    f"Trim end (seconds) - clip {i + 1}", min_value=0.1, value=5.0, step=0.1, key=f"trim_end_{i}"
                )
            col_vol, col_mute = st.columns(2)
            with col_vol:
                video_volume = st.slider(
                    f"Original video volume - clip {i + 1}",
                    min_value=0.0,
                    max_value=1.0,
                    value=1.0,
                    step=0.05,
                    key=f"video_volume_{i}",
                )
            with col_mute:
                video_muted = st.checkbox(f"Mute original video audio - clip {i + 1}", value=False, key=f"video_muted_{i}")
            col_fin, col_fout = st.columns(2)
            with col_fin:
                video_fade_in = st.number_input(
                    f"Video fade-in (seconds) - clip {i + 1}", min_value=0.0, value=0.0, step=0.5, key=f"video_fade_in_{i}"
                )
            with col_fout:
                video_fade_out = st.number_input(
                    f"Video fade-out (seconds) - clip {i + 1}", min_value=0.0, value=0.0, step=0.5, key=f"video_fade_out_{i}"
                )
            clips.append(
                {
                    "video_file": video_file,
                    "trim_start": float(trim_start),
                    "trim_end": float(trim_end),
                    "video_volume": float(video_volume),
                    "video_muted": bool(video_muted),
                    "video_fade_in": float(video_fade_in),
                    "video_fade_out": float(video_fade_out),
                }
            )

        text_overlays: List[Dict[str, Any]] = []
        if num_text_overlays:
            st.subheader("Text Styling")
        for i in range(int(num_text_overlays)):
            st.markdown(f"**Text overlay {i + 1}**")
            text_overlay = st.text_input(f"Text overlay {i + 1}", key=f"text_overlay_{i}")
            col_start, col_dur = st.columns(2)
            with col_start:
                text_start = st.number_input(
                    f"Start offset (seconds) - text {i + 1}", min_value=0.0, value=0.0, step=0.5, key=f"text_start_{i}"
                )
            with col_dur:
                text_duration = st.number_input(
                    f"Duration (seconds) - text {i + 1}", min_value=0.1, value=5.0, step=0.5, key=f"text_duration_{i}"
                )
            col_font, col_size = st.columns(2)
            with col_font:
                font_family = st.selectbox("Font family", FONT_FAMILIES, index=0, key=f"font_family_{i}")
            with col_size:
                font_size = st.number_input("Font size", min_value=8, max_value=200, value=32, step=1, key=f"font_size_{i}")
            col_color, col_bg = st.columns(2)
            with col_color:
                text_color = st.color_picker("Text color", value="#FFFFFF", key=f"text_color_{i}")
            with col_bg:
                text_bg_enabled = st.checkbox("Add text background", value=False, key=f"text_bg_enabled_{i}")
                text_bg_color = st.color_picker(
                    "Text background color", value="#000000", disabled=not text_bg_enabled, key=f"text_bg_color_{i}"
                )
            col_vpos, col_hpos = st.columns(2)
            with col_vpos:
                text_vertical_position = st.selectbox(
                    "Text vertical position", VERTICAL_POSITIONS, index=2, key=f"text_vpos_{i}"
                )
            with col_hpos:
                text_horizontal_position = st.selectbox(
                    "Text horizontal position", HORIZONTAL_POSITIONS, index=1, key=f"text_hpos_{i}"
                )
            text_style = st.selectbox("Text style preset", TEXT_STYLES, index=0, key=f"text_style_{i}")
            text_overlays.append(
                {
                    "text": text_overlay.strip(),
                    "start": float(text_start),
                    "duration": float(text_duration),
                    "font_family": None if font_family == "Default" else font_family,
                    "font_size": int(font_size),
                    "color": text_color,
                    "bg_color": text_bg_color if text_bg_enabled else None,
                    "position": f"{text_vertical_position}-{text_horizontal_position}",
                    "style": text_style,
                }
            )

        audio_tracks: List[Dict[str, Any]] = []
        if num_audio_tracks:
            st.subheader("Audio")
        for i in range(int(num_audio_tracks)):
            st.markdown(f"**Audio track {i + 1}**")
            music_url = st.text_input(f"Audio URL {i + 1}", placeholder="https://...", key=f"music_url_{i}")
            music_volume = st.slider("Volume", min_value=0.0, max_value=1.0, value=0.4, step=0.05, key=f"music_volume_{i}")
            col_fade_in, col_fade_out = st.columns(2)
            with col_fade_in:
                music_fade_in = st.number_input("Fade-in (seconds)", min_value=0.0, value=1.0, step=0.5, key=f"music_fade_in_{i}")
            with col_fade_out:
                music_fade_out = st.number_input("Fade-out (seconds)", min_value=0.0, value=1.0, step=0.5, key=f"music_fade_out_{i}")
            music_start = st.number_input("Start offset (seconds)", min_value=0.0, value=0.0, step=0.5, key=f"music_start_{i}")
            audio_tracks.append(
                {
                    "url": music_url.strip() or None,
                    "volume": float(music_volume),
                    "fade_in": float(music_fade_in),
                    "fade_out": float(music_fade_out),
                    "start": float(music_start),
                }
            )

        image_overlays: List[Dict[str, Any]] = []
        if num_image_overlays:
            st.subheader("Watermark / Logo overlays")
        for i in range(int(num_image_overlays)):
            st.markdown(f"**Image overlay {i + 1}**")
            watermark_file = st.file_uploader(
                f"Watermark image {i + 1}", type=["png", "jpg", "jpeg", "webp"], key=f"watermark_file_{i}"
            )
            col_wpos, col_wop = st.columns(2)
            with col_wpos:
                watermark_position = st.selectbox(
                    "Position", WATERMARK_POSITIONS, index=2, key=f"watermark_position_{i}"
                )
            with col_wop:
                watermark_opacity = st.slider(
                    "Opacity", min_value=0.0, max_value=1.0, value=1.0, step=0.05, key=f"watermark_opacity_{i}"
                )
            col_wstart, col_wdur = st.columns(2)
            with col_wstart:
                watermark_start = st.number_input(
                    "Start offset (seconds)", min_value=0.0, value=0.0, step=0.5, key=f"watermark_start_{i}"
                )
            with col_wdur:
                watermark_duration = st.number_input(
                    "Duration (seconds, 0 = whole video)", min_value=0.0, value=0.0, step=0.5, key=f"watermark_duration_{i}"
                )
            image_overlays.append(
                {
                    "file": watermark_file,
                    "position": watermark_position,
                    "opacity": float(watermark_opacity),
                    "start": float(watermark_start),
                    "duration": float(watermark_duration) or None,
                }
            )

        st.subheader("AI Voiceover")
        voiceover_enabled = st.checkbox("Add AI voiceover narration", value=False)
        voiceover_text = st.text_area(
            "Narration script", disabled=not voiceover_enabled, placeholder="Text to be spoken aloud"
        )
        col_voice, col_voice_model = st.columns(2)
        with col_voice:
            voiceover_voice = st.selectbox("Voice", VOICES, index=0, disabled=not voiceover_enabled)
        with col_voice_model:
            voiceover_model = st.selectbox("Voice model", VOICE_MODELS, index=0, disabled=not voiceover_enabled)

        st.subheader("Auto Captions / Subtitles")
        subtitles_enabled = st.checkbox("Add automatic captions", value=False)
        col_sub_lang, col_sub_model = st.columns(2)
        with col_sub_lang:
            subtitle_language = st.selectbox(
                "Caption language", SUBTITLE_LANGUAGES, index=0, disabled=not subtitles_enabled
            )
        with col_sub_model:
            subtitle_model = st.selectbox(
                "Transcription model", SUBTITLE_MODELS, index=0, disabled=not subtitles_enabled
            )
        col_sub_style, col_sub_size = st.columns(2)
        with col_sub_style:
            subtitle_style = st.selectbox(
                "Caption style", SUBTITLE_STYLES, index=0, disabled=not subtitles_enabled
            )
        with col_sub_size:
            subtitle_font_size = st.number_input(
                "Caption font size", min_value=8, max_value=200, value=48, step=1, disabled=not subtitles_enabled
            )
        subtitle_position = st.selectbox(
            "Caption position", VERTICAL_POSITIONS, index=2, key="subtitle_position", disabled=not subtitles_enabled
        )

        submitted = st.form_submit_button("Render Video", use_container_width=True)

    return {
        "submitted": submitted,
        "api_key": api_key,
        "resolution": resolution,
        "quality": quality,
        "speed": float(speed),
        "rotate": int(rotate),
        "zoom_level": float(zoom_level) if zoom_enabled else None,
        "brightness": float(brightness),
        "contrast": float(contrast),
        "saturation": float(saturation),
        "color_preset": None if color_preset == "none" else color_preset,
        "duck_level": float(duck_level) if duck_enabled else None,
        "transition_type": None if transition_type == "none" else transition_type,
        "transition_duration": float(transition_duration),
        "clips": clips,
        "text_overlays": text_overlays,
        "audio_tracks": audio_tracks,
        "image_overlays": image_overlays,
        "voiceover": (
            {
                "text": voiceover_text.strip(),
                "voice": voiceover_voice,
                "model": voiceover_model,
            }
            if voiceover_enabled and voiceover_text.strip()
            else None
        ),
        "subtitles": (
            {
                "language": None if subtitle_language == "auto" else subtitle_language,
                "model": subtitle_model,
                "style": subtitle_style,
                "font_size": int(subtitle_font_size),
                "position": subtitle_position,
            }
            if subtitles_enabled
            else None
        ),
    }


def render_result(result: Dict[str, Any]) -> None:
    if result.get("status") != "done":
        st.error(result.get("error", "Render failed"))
        return

    url = result.get("url")
    st.success("Render complete")
    st.video(url)
    st.markdown(f"[Download rendered video]({url})")
