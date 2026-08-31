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
    if not state["api_key"]:
        st.error("Please enter your JSON2Video API key.")
    elif state["video_file"] is None:
        st.error("Please upload a video file.")
    elif state["trim_end"] <= state["trim_start"]:
        st.error("Trim end must be greater than trim start.")
    else:
        with st.spinner("Uploading and rendering video..."):
            try:
                result = api_client.fetch_data(
                    api_key=state["api_key"],
                    video_bytes=state["video_file"].getvalue(),
                    trim_start=state["trim_start"],
                    trim_end=state["trim_end"],
                    resolution=state["resolution"],
                    quality=state["quality"],
                    video_volume=state["video_volume"],
                    video_muted=state["video_muted"],
                    video_fade_in=state["video_fade_in"],
                    video_fade_out=state["video_fade_out"],
                    text_overlay=state["text_overlay"],
                    font_family=state["font_family"],
                    font_size=state["font_size"],
                    text_color=state["text_color"],
                    text_bg_color=state["text_bg_color"],
                    text_position=state["text_position"],
                    text_style=state["text_style"],
                    music_url=state["music_url"],
                    music_volume=state["music_volume"],
                    music_fade_in=state["music_fade_in"],
                    music_fade_out=state["music_fade_out"],
                    music_start=state["music_start"],
                    watermark_bytes=state["watermark_file"].getvalue() if state["watermark_file"] else None,
                    watermark_position=state["watermark_position"],
                    watermark_opacity=state["watermark_opacity"],
                )
            except Exception as exc:
                st.error(f"Render request failed: {exc}")
            else:
                render_result(result)
else:
    st.info("Enter your JSON2Video API key, upload a video, configure edits, then click Render Video.")
