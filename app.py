from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import api_client
from ui import render_editor_form, render_result

st.set_page_config(page_title="JSON2Video Video Editor", page_icon="🎬", layout="centered")

css_path = Path(__file__).parent / "static" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

state = render_editor_form()

if state["submitted"]:
    missing_clip = any(clip["video_file"] is None for clip in state["clips"])
    invalid_trim = any(clip["trim_end"] <= clip["trim_start"] for clip in state["clips"])
    missing_resolution = state["resolution"] == "custom" and (not state["width"] or not state["height"])

    invalid_graphic_overlay = False
    graphic_overlay_error = None
    for overlay in state["graphic_overlays"]:
        if overlay["type"] == "component" and not overlay["component"]:
            invalid_graphic_overlay = True
            graphic_overlay_error = "Every component overlay needs a component ID."
        if overlay["type"] == "html" and not overlay["html"]:
            invalid_graphic_overlay = True
            graphic_overlay_error = "Every HTML overlay needs HTML content."
        if overlay["settings_raw"]:
            try:
                json.loads(overlay["settings_raw"])
            except ValueError:
                invalid_graphic_overlay = True
                graphic_overlay_error = "Component settings must be valid JSON."

    if not state["api_key"]:
        st.error("Please enter your JSON2Video API key.")
    elif not state["clips"]:
        st.error("Please add at least one video clip.")
    elif missing_clip:
        st.error("Please upload a video file for every clip.")
    elif invalid_trim:
        st.error("Trim end must be greater than trim start for every clip.")
    elif missing_resolution:
        st.error("Please provide a custom width and height, or choose a resolution preset.")
    elif invalid_graphic_overlay:
        st.error(graphic_overlay_error)
    else:
        with st.spinner("Uploading and rendering video..."):
            try:
                clips_payload = [
                    {
                        "video_bytes": clip["video_file"].getvalue(),
                        "trim_start": clip["trim_start"],
                        "trim_end": clip["trim_end"],
                        "video_volume": clip["video_volume"],
                        "video_muted": clip["video_muted"],
                        "video_fade_in": clip["video_fade_in"],
                        "video_fade_out": clip["video_fade_out"],
                        "background": {
                            "mode": (
                                "color"
                                if clip["background_mode"] == "Solid color"
                                else "image"
                                if clip["background_mode"] == "Background image"
                                else "none"
                            ),
                            "color": clip["background_color"],
                            "image_bytes": (
                                clip["background_image_file"].getvalue()
                                if clip["background_image_file"]
                                else None
                            ),
                        },
                    }
                    for clip in state["clips"]
                ]
                image_overlays_payload = [
                    {
                        "image_bytes": overlay["file"].getvalue() if overlay["file"] else None,
                        "position": overlay["position"],
                        "opacity": overlay["opacity"],
                        "start": overlay["start"],
                        "duration": overlay["duration"],
                    }
                    for overlay in state["image_overlays"]
                    if overlay["file"] is not None
                ]

                subtitles_payload = None
                if state["subtitles"]:
                    subtitles_payload = dict(state["subtitles"])
                    captions_source = subtitles_payload.pop("captions_source", "Auto-transcribe")
                    captions_file = subtitles_payload.pop("captions_file", None)
                    captions_text = subtitles_payload.pop("captions_text", None)
                    if captions_source == "Upload SRT/VTT file" and captions_file is not None:
                        subtitles_payload["captions_file_bytes"] = captions_file.getvalue()
                        subtitles_payload["captions_file_name"] = captions_file.name
                    elif captions_source == "Paste SRT/VTT text" and captions_text:
                        subtitles_payload["captions"] = captions_text

                extra_overlays_payload = [
                    {
                        "type": overlay["type"],
                        "component": overlay["component"],
                        "settings": json.loads(overlay["settings_raw"]) if overlay["settings_raw"] else None,
                        "html": overlay["html"],
                        "tailwind": overlay["tailwind"],
                        "position": overlay["position"],
                        "start": overlay["start"],
                        "duration": overlay["duration"],
                    }
                    for overlay in state["graphic_overlays"]
                ]

                result = api_client.fetch_data(
                    api_key=state["api_key"],
                    clips=clips_payload,
                    resolution=state["resolution"],
                    quality=state["quality"],
                    width=state["width"],
                    height=state["height"],
                    speed=state["speed"],
                    rotate=state["rotate"],
                    zoom_level=state["zoom_level"],
                    brightness=state["brightness"],
                    contrast=state["contrast"],
                    saturation=state["saturation"],
                    color_preset=state["color_preset"],
                    duck_level=state["duck_level"],
                    flip_horizontal=state["flip_horizontal"],
                    flip_vertical=state["flip_vertical"],
                    crop=state["crop"],
                    pan=state["pan"],
                    pan_distance=state["pan_distance"],
                    pan_crop=state["pan_crop"],
                    chroma_key=state["chroma_key"],
                    transition_type=state["transition_type"],
                    transition_duration=state["transition_duration"],
                    text_overlays=state["text_overlays"],
                    audio_tracks=state["audio_tracks"],
                    image_overlays=image_overlays_payload,
                    voiceovers=state["voice_segments"],
                    subtitles=subtitles_payload,
                    extra_overlays=extra_overlays_payload,
                )
            except Exception as exc:
                st.error(f"Render request failed: {exc}")
            else:
                render_result(result)
else:
    st.info("Enter your JSON2Video API key, upload a video, configure edits, then click Render Video.")
