from __future__ import annotations

from typing import Any, Dict

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


def render_editor_form() -> Dict[str, Any]:
    st.title("JSON2Video Video Editor")
    st.caption("Upload a video, set simple edits, and render using your JSON2Video API key.")

    with st.form("video-editor-form"):
        api_key = st.text_input("JSON2Video API key", type="password")
        video_file = st.file_uploader("Upload video", type=["mp4", "mov", "webm", "m4v"])

        st.subheader("Editing Controls")
        trim_start = st.number_input("Trim start (seconds)", min_value=0.0, value=0.0, step=0.1)
        trim_end = st.number_input("Trim end (seconds)", min_value=0.1, value=5.0, step=0.1)

        st.subheader("Video Quality")
        col_res, col_qual = st.columns(2)
        with col_res:
            resolution = st.selectbox("Resolution", RESOLUTIONS, index=0)
        with col_qual:
            quality = st.selectbox("Quality", QUALITIES, index=1)
        video_volume = st.slider("Original video volume", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
        video_muted = st.checkbox("Mute original video audio", value=False)
        video_fade_in = st.number_input("Video fade-in (seconds)", min_value=0.0, value=0.0, step=0.5)
        video_fade_out = st.number_input("Video fade-out (seconds)", min_value=0.0, value=0.0, step=0.5)

        st.subheader("Text Styling")
        text_overlay = st.text_input("Text overlay")
        col_font, col_size = st.columns(2)
        with col_font:
            font_family = st.selectbox("Font family", FONT_FAMILIES, index=0)
        with col_size:
            font_size = st.number_input("Font size", min_value=8, max_value=200, value=32, step=1)
        col_color, col_bg = st.columns(2)
        with col_color:
            text_color = st.color_picker("Text color", value="#FFFFFF")
        with col_bg:
            text_bg_enabled = st.checkbox("Add text background", value=False)
            text_bg_color = st.color_picker("Text background color", value="#000000", disabled=not text_bg_enabled)
        col_vpos, col_hpos = st.columns(2)
        with col_vpos:
            text_vertical_position = st.selectbox("Text vertical position", VERTICAL_POSITIONS, index=2)
        with col_hpos:
            text_horizontal_position = st.selectbox("Text horizontal position", HORIZONTAL_POSITIONS, index=1)
        text_style = st.selectbox("Text style preset", TEXT_STYLES, index=0)

        st.subheader("Audio")
        music_url = st.text_input("Optional music URL", placeholder="https://...")
        music_volume = st.slider("Music volume", min_value=0.0, max_value=1.0, value=0.4, step=0.05)
        col_fade_in, col_fade_out = st.columns(2)
        with col_fade_in:
            music_fade_in = st.number_input("Music fade-in (seconds)", min_value=0.0, value=1.0, step=0.5)
        with col_fade_out:
            music_fade_out = st.number_input("Music fade-out (seconds)", min_value=0.0, value=1.0, step=0.5)
        music_start = st.number_input("Music start offset (seconds)", min_value=0.0, value=0.0, step=0.5)

        st.subheader("Watermark / Logo")
        watermark_file = st.file_uploader("Watermark image (optional)", type=["png", "jpg", "jpeg", "webp"])
        col_wpos, col_wop = st.columns(2)
        with col_wpos:
            watermark_position = st.selectbox("Watermark position", WATERMARK_POSITIONS, index=2)
        with col_wop:
            watermark_opacity = st.slider("Watermark opacity", min_value=0.0, max_value=1.0, value=1.0, step=0.05)

        submitted = st.form_submit_button("Render Video", use_container_width=True)

    return {
        "submitted": submitted,
        "api_key": api_key,
        "video_file": video_file,
        "trim_start": float(trim_start),
        "trim_end": float(trim_end),
        "resolution": resolution,
        "quality": quality,
        "video_volume": float(video_volume),
        "video_muted": bool(video_muted),
        "video_fade_in": float(video_fade_in),
        "video_fade_out": float(video_fade_out),
        "text_overlay": text_overlay.strip(),
        "font_family": None if font_family == "Default" else font_family,
        "font_size": int(font_size),
        "text_color": text_color,
        "text_bg_color": text_bg_color if text_bg_enabled else None,
        "text_position": f"{text_vertical_position}-{text_horizontal_position}",
        "text_style": text_style,
        "music_url": music_url.strip() or None,
        "music_volume": float(music_volume),
        "music_fade_in": float(music_fade_in),
        "music_fade_out": float(music_fade_out),
        "music_start": float(music_start),
        "watermark_file": watermark_file,
        "watermark_position": watermark_position,
        "watermark_opacity": float(watermark_opacity),
    }


def render_result(result: Dict[str, Any]) -> None:
    if result.get("status") != "done":
        st.error(result.get("error", "Render failed"))
        return

    url = result.get("url")
    st.success("Render complete")
    st.video(url)
    st.markdown(f"[Download rendered video]({url})")
