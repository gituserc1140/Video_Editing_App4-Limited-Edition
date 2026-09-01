from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st


FONT_FAMILIES = ["Default", "Roboto", "Open Sans", "Montserrat", "Oswald", "Poppins", "Lato"]
TEXT_STYLES = ["minimal", "classic", "elegant", "bold", "subtitle"]
VERTICAL_POSITIONS = ["top", "center", "bottom"]
HORIZONTAL_POSITIONS = ["left", "center", "right"]
RESOLUTIONS = ["sd", "hd", "full-hd", "custom"]
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
MAX_VOICE_SEGMENTS = 3
MAX_GRAPHIC_OVERLAYS = 3
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
CAPTIONS_SOURCES = ["Auto-transcribe", "Upload SRT/VTT file", "Paste SRT/VTT text"]
BACKGROUND_MODES = ["None (transparent)", "Solid color", "Background image"]
PAN_DIRECTIONS = ["left", "right", "top", "bottom"]
PAN_CROP_OPTIONS = ["none", "in", "out"]
GRAPHIC_OVERLAY_TYPES = ["component", "html"]


def render_editor_form() -> Dict[str, Any]:
    st.title("JSON2Video Video Editor")
    st.caption("Upload a video, set simple edits, and render using your JSON2Video API key.")

    # Item counts are chosen outside the form so the form widget layout can react to them
    # before submission (Streamlit forms don't rerun until submitted).
    st.subheader("Clips")
    num_clips = st.number_input(
        "Number of video clips", min_value=1, max_value=MAX_CLIPS, value=1, step=1
    )

    if "clip_order" not in st.session_state:
        st.session_state["clip_order"] = list(range(MAX_CLIPS))
    clip_order: List[int] = st.session_state["clip_order"]
    active_clip_ids = clip_order[: int(num_clips)]

    if int(num_clips) > 1:
        st.caption(
            "Reorder clips below (native drag-and-drop isn't available in Streamlit, "
            "so use the ↑/↓ buttons instead)."
        )
        for display_pos, clip_id in enumerate(active_clip_ids):
            col_label, col_up, col_down = st.columns([6, 1, 1])
            col_label.markdown(f"Position {display_pos + 1}: clip editor #{clip_id + 1}")
            if col_up.button("↑", key=f"move_up_{clip_id}", disabled=display_pos == 0):
                idx = clip_order.index(clip_id)
                clip_order[idx - 1], clip_order[idx] = clip_order[idx], clip_order[idx - 1]
                st.rerun()
            if col_down.button("↓", key=f"move_down_{clip_id}", disabled=display_pos == len(active_clip_ids) - 1):
                idx = clip_order.index(clip_id)
                clip_order[idx + 1], clip_order[idx] = clip_order[idx], clip_order[idx + 1]
                st.rerun()

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
    col_voice, col_graphic = st.columns(2)
    with col_voice:
        num_voice_segments = st.number_input(
            "Voiceover/narration segments", min_value=0, max_value=MAX_VOICE_SEGMENTS, value=0, step=1
        )
    with col_graphic:
        num_graphic_overlays = st.number_input(
            "Component/HTML graphic overlays", min_value=0, max_value=MAX_GRAPHIC_OVERLAYS, value=0, step=1
        )

    with st.form("video-editor-form"):
        api_key = st.text_input("JSON2Video API key", type="password")

        st.subheader("Video Quality")
        col_res, col_qual = st.columns(2)
        with col_res:
            resolution = st.selectbox("Resolution", RESOLUTIONS, index=0)
        with col_qual:
            quality = st.selectbox("Quality", QUALITIES, index=1)
        col_width, col_height = st.columns(2)
        with col_width:
            custom_width = st.number_input(
                "Custom width (px)", min_value=50, max_value=7680, value=1280, step=10,
                disabled=resolution != "custom",
            )
        with col_height:
            custom_height = st.number_input(
                "Custom height (px)", min_value=50, max_value=7680, value=720, step=10,
                disabled=resolution != "custom",
            )

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
        col_flip_h, col_flip_v = st.columns(2)
        with col_flip_h:
            flip_horizontal = st.checkbox("Flip horizontal (mirror left/right)", value=False)
        with col_flip_v:
            flip_vertical = st.checkbox("Flip vertical (mirror top/bottom)", value=False)
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

        st.subheader("Crop, Pan & Chroma Key")
        st.caption("Applied to every video clip.")
        crop_enabled = st.checkbox("Enable crop", value=False)
        col_cx, col_cy, col_cw, col_ch = st.columns(4)
        with col_cx:
            crop_x = st.number_input("Crop X", min_value=0, value=0, step=10, disabled=not crop_enabled)
        with col_cy:
            crop_y = st.number_input("Crop Y", min_value=0, value=0, step=10, disabled=not crop_enabled)
        with col_cw:
            crop_width = st.number_input("Crop width", min_value=1, value=640, step=10, disabled=not crop_enabled)
        with col_ch:
            crop_height = st.number_input("Crop height", min_value=1, value=360, step=10, disabled=not crop_enabled)

        pan_enabled = st.checkbox("Enable pan", value=False)
        col_pdir, col_pdist, col_pcrop = st.columns(3)
        with col_pdir:
            pan_direction = st.selectbox("Pan direction", PAN_DIRECTIONS, index=0, disabled=not pan_enabled)
        with col_pdist:
            pan_distance = st.number_input(
                "Pan distance (pixels)", min_value=0, value=300, step=10, disabled=not pan_enabled
            )
        with col_pcrop:
            pan_crop = st.selectbox("Pan + zoom", PAN_CROP_OPTIONS, index=0, disabled=not pan_enabled)

        chroma_enabled = st.checkbox("Enable chroma key (green screen removal)", value=False)
        col_ckcolor, col_cksim, col_ckblend = st.columns(3)
        with col_ckcolor:
            chroma_color = st.color_picker("Key color", value="#00B140", disabled=not chroma_enabled)
        with col_cksim:
            chroma_similarity = st.slider(
                "Similarity", min_value=0.0, max_value=1.0, value=0.4, step=0.05, disabled=not chroma_enabled
            )
        with col_ckblend:
            chroma_blend = st.slider(
                "Edge blend", min_value=0.0, max_value=1.0, value=0.1, step=0.05, disabled=not chroma_enabled
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
        for i in active_clip_ids:
            display_pos = active_clip_ids.index(i)
            st.markdown(f"**Clip {display_pos + 1}**")
            video_file = st.file_uploader(
                f"Upload video for clip {display_pos + 1}",
                type=["mp4", "mov", "webm", "m4v"],
                key=f"clip_file_{i}",
            )
            col_start, col_end = st.columns(2)
            with col_start:
                trim_start = st.number_input(
                    f"Trim start (seconds) - clip {display_pos + 1}", min_value=0.0, value=0.0, step=0.1, key=f"trim_start_{i}"
                )
            with col_end:
                trim_end = st.number_input(
                    f"Trim end (seconds) - clip {display_pos + 1}", min_value=0.1, value=5.0, step=0.1, key=f"trim_end_{i}"
                )
            col_vol, col_mute = st.columns(2)
            with col_vol:
                video_volume = st.slider(
                    f"Original video volume - clip {display_pos + 1}",
                    min_value=0.0,
                    max_value=1.0,
                    value=1.0,
                    step=0.05,
                    key=f"video_volume_{i}",
                )
            with col_mute:
                video_muted = st.checkbox(f"Mute original video audio - clip {display_pos + 1}", value=False, key=f"video_muted_{i}")
            col_fin, col_fout = st.columns(2)
            with col_fin:
                video_fade_in = st.number_input(
                    f"Video fade-in (seconds) - clip {display_pos + 1}", min_value=0.0, value=0.0, step=0.5, key=f"video_fade_in_{i}"
                )
            with col_fout:
                video_fade_out = st.number_input(
                    f"Video fade-out (seconds) - clip {display_pos + 1}", min_value=0.0, value=0.0, step=0.5, key=f"video_fade_out_{i}"
                )
            background_mode = st.selectbox(
                f"Scene background - clip {display_pos + 1}", BACKGROUND_MODES, index=0, key=f"background_mode_{i}"
            )
            background_color = st.color_picker(
                f"Background color - clip {display_pos + 1}",
                value="#000000",
                disabled=background_mode != "Solid color",
                key=f"background_color_{i}",
            )
            background_image_file = st.file_uploader(
                f"Background image - clip {display_pos + 1}",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"background_image_{i}",
                disabled=background_mode != "Background image",
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
                    "background_mode": background_mode,
                    "background_color": background_color,
                    "background_image_file": background_image_file,
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

        voice_segments: List[Dict[str, Any]] = []
        if num_voice_segments:
            st.subheader("AI Voiceover / Narration Segments")
        for i in range(int(num_voice_segments)):
            st.markdown(f"**Narration segment {i + 1}**")
            segment_text = st.text_area(
                f"Narration script {i + 1}", placeholder="Text to be spoken aloud", key=f"voice_text_{i}"
            )
            col_voice, col_voice_model = st.columns(2)
            with col_voice:
                segment_voice = st.selectbox("Voice", VOICES, index=0, key=f"voice_select_{i}")
            with col_voice_model:
                segment_model = st.selectbox("Voice model", VOICE_MODELS, index=0, key=f"voice_model_{i}")
            segment_start = st.number_input(
                f"Start offset (seconds) - segment {i + 1}", min_value=0.0, value=0.0, step=0.5, key=f"voice_start_{i}"
            )
            voice_segments.append(
                {
                    "text": segment_text.strip(),
                    "voice": segment_voice,
                    "model": segment_model,
                    "start": float(segment_start),
                }
            )

        graphic_overlays: List[Dict[str, Any]] = []
        if num_graphic_overlays:
            st.subheader("Component / HTML Graphic Overlays")
            st.caption("Pre-built animated components (e.g. lower-thirds) or fully custom HTML/CSS overlays.")
        for i in range(int(num_graphic_overlays)):
            st.markdown(f"**Graphic overlay {i + 1}**")
            overlay_type = st.selectbox("Overlay type", GRAPHIC_OVERLAY_TYPES, index=0, key=f"graphic_type_{i}")
            component_id = ""
            component_settings = ""
            html_content = ""
            tailwind = False
            position = "bottom-left"
            if overlay_type == "component":
                component_id = st.text_input(
                    "Component ID (e.g. basic/050)", key=f"graphic_component_id_{i}"
                )
                component_settings = st.text_area(
                    "Component settings (JSON object, optional)",
                    placeholder='{"headline": "Ana López", "subline": "Product Manager"}',
                    key=f"graphic_component_settings_{i}",
                )
            else:
                html_content = st.text_area(
                    "HTML/CSS content", placeholder="<div style='...'>Your overlay</div>", key=f"graphic_html_{i}"
                )
                tailwind = st.checkbox("Enable Tailwind CSS classes", value=False, key=f"graphic_tailwind_{i}")
                position = st.selectbox("Position", WATERMARK_POSITIONS, index=6, key=f"graphic_position_{i}")
            col_gstart, col_gdur = st.columns(2)
            with col_gstart:
                overlay_start = st.number_input(
                    "Start offset (seconds)", min_value=0.0, value=0.0, step=0.5, key=f"graphic_start_{i}"
                )
            with col_gdur:
                overlay_duration = st.number_input(
                    "Duration (seconds, 0 = whole video)", min_value=0.0, value=0.0, step=0.5, key=f"graphic_duration_{i}"
                )
            graphic_overlays.append(
                {
                    "type": overlay_type,
                    "component": component_id.strip() or None,
                    "settings_raw": component_settings.strip() or None,
                    "html": html_content.strip() or None,
                    "tailwind": tailwind,
                    "position": position,
                    "start": float(overlay_start),
                    "duration": float(overlay_duration) or None,
                }
            )

        st.subheader("Auto Captions / Subtitles")
        subtitles_enabled = st.checkbox("Add captions", value=False)
        captions_source = st.selectbox(
            "Caption source", CAPTIONS_SOURCES, index=0, disabled=not subtitles_enabled
        )
        col_sub_lang, col_sub_model = st.columns(2)
        with col_sub_lang:
            subtitle_language = st.selectbox(
                "Caption language",
                SUBTITLE_LANGUAGES,
                index=0,
                disabled=not subtitles_enabled or captions_source != "Auto-transcribe",
            )
        with col_sub_model:
            subtitle_model = st.selectbox(
                "Transcription model",
                SUBTITLE_MODELS,
                index=0,
                disabled=not subtitles_enabled or captions_source != "Auto-transcribe",
            )
        captions_file = st.file_uploader(
            "Caption file (.srt or .vtt)",
            type=["srt", "vtt"],
            disabled=not subtitles_enabled or captions_source != "Upload SRT/VTT file",
        )
        captions_text = st.text_area(
            "Paste SRT/VTT caption content",
            disabled=not subtitles_enabled or captions_source != "Paste SRT/VTT text",
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
        "width": int(custom_width) if resolution == "custom" else None,
        "height": int(custom_height) if resolution == "custom" else None,
        "speed": float(speed),
        "rotate": int(rotate),
        "zoom_level": float(zoom_level) if zoom_enabled else None,
        "flip_horizontal": bool(flip_horizontal),
        "flip_vertical": bool(flip_vertical),
        "brightness": float(brightness),
        "contrast": float(contrast),
        "saturation": float(saturation),
        "color_preset": None if color_preset == "none" else color_preset,
        "duck_level": float(duck_level) if duck_enabled else None,
        "crop": (
            {
                "x": int(crop_x),
                "y": int(crop_y),
                "width": int(crop_width),
                "height": int(crop_height),
            }
            if crop_enabled
            else None
        ),
        "pan": pan_direction if pan_enabled else None,
        "pan_distance": int(pan_distance) if pan_enabled else None,
        "pan_crop": (None if pan_crop == "none" else pan_crop) if pan_enabled else None,
        "chroma_key": (
            {
                "color": chroma_color,
                "similarity": float(chroma_similarity),
                "blend": float(chroma_blend),
            }
            if chroma_enabled
            else None
        ),
        "transition_type": None if transition_type == "none" else transition_type,
        "transition_duration": float(transition_duration),
        "clips": clips,
        "text_overlays": text_overlays,
        "audio_tracks": audio_tracks,
        "image_overlays": image_overlays,
        "voice_segments": voice_segments,
        "graphic_overlays": graphic_overlays,
        "subtitles": (
            {
                "captions_source": captions_source,
                "language": None if subtitle_language == "auto" else subtitle_language,
                "model": subtitle_model,
                "captions_file": captions_file,
                "captions_text": captions_text.strip() or None,
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
