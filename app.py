from __future__ import annotations

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

    if not state["api_key"]:
        st.error("Please enter your JSON2Video API key.")
    elif not state["clips"]:
        st.error("Please add at least one video clip.")
    elif missing_clip:
        st.error("Please upload a video file for every clip.")
    elif invalid_trim:
        st.error("Trim end must be greater than trim start for every clip.")
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

                result = api_client.fetch_data(
                    api_key=state["api_key"],
                    clips=clips_payload,
                    resolution=state["resolution"],
                    quality=state["quality"],
                    speed=state["speed"],
                    rotate=state["rotate"],
                    zoom_level=state["zoom_level"],
                    brightness=state["brightness"],
                    contrast=state["contrast"],
                    saturation=state["saturation"],
                    color_preset=state["color_preset"],
                    duck_level=state["duck_level"],
                    transition_type=state["transition_type"],
                    transition_duration=state["transition_duration"],
                    text_overlays=state["text_overlays"],
                    audio_tracks=state["audio_tracks"],
                    image_overlays=image_overlays_payload,
                )
            except Exception as exc:
                st.error(f"Render request failed: {exc}")
            else:
                render_result(result)
else:
    st.info("Enter your JSON2Video API key, upload a video, configure edits, then click Render Video.")
