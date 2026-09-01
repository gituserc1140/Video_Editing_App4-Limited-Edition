from __future__ import annotations

import mimetypes
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from config import settings


MEDIA_UPLOAD_ENDPOINT = "/v2/media/file"
MOVIE_CREATE_ENDPOINT = "/v2/movies"
MOVIE_STATUS_ENDPOINT = "/v2/movies"


def _extract(data: Any, *paths: str) -> Optional[Any]:
    for path in paths:
        current = data
        ok = True
        for key in path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                ok = False
                break
        if ok and current is not None:
            return current
    return None


def _error_detail(body: Dict[str, Any]) -> Optional[str]:
    message = _extract(body, "message", "movie.message", "error")
    if isinstance(message, str) and message:
        return message
    if message is not None:
        return str(message)
    return None


def _render_output_url(data: Any) -> Optional[str]:
    url = _extract(data, "movie.url", "url")
    if not isinstance(url, str):
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def _request(
    base_url: str,
    method: str,
    path: str,
    api_key: str,
    *,
    json_payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
) -> Any:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {"x-api-key": api_key.strip(), "Accept": "application/json"}
    if json_payload is not None:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json_payload,
            params=params,
            timeout=timeout or settings.DEFAULT_TIMEOUT,
            allow_redirects=False,
        )
    except requests.exceptions.ConnectionError as exc:
        raise requests.exceptions.ConnectionError(
            f"Could not reach {base_url} ({method.upper()} {path}); check your network connection "
            "and that this environment allows outbound requests to the JSON2Video API host",
            response=getattr(exc, "response", None),
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise requests.exceptions.Timeout(
            f"Timed out connecting to {base_url} ({method.upper()} {path}); the JSON2Video API host "
            "may be unreachable from this environment",
            response=getattr(exc, "response", None),
        ) from exc
    if response.status_code in {301, 302, 303, 307, 308}:
        location = response.headers.get("Location", "an unknown location")
        raise requests.HTTPError(
            f"JSON2Video redirected {method.upper()} {path} to {location}; "
            "check that the configured API base URL is correct",
            response=response,
        )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = None
        try:
            body = response.json()
        except ValueError:
            body = None
        if isinstance(body, dict):
            detail = _error_detail(body)
        if response.status_code == 401:
            mismatch_hint = "Confirm your JSON2Video API key is correct and has remaining quota"
            detail = f"{detail}; {mismatch_hint}" if detail else mismatch_hint
        if detail:
            raise requests.HTTPError(f"{exc} - {detail}", response=response) from exc
        raise
    if not response.text:
        return {}

    try:
        return response.json()
    except ValueError:
        return response.text


def _upload_media_source(api_key: str, file_name: str, file_bytes: bytes, default_content_type: str) -> str:
    content_type = mimetypes.guess_type(file_name)[0] or default_content_type
    upload_response = _request(
        settings.JSON2VIDEO_BASE_URL,
        "POST",
        MEDIA_UPLOAD_ENDPOINT,
        api_key,
        json_payload={
            "name": file_name,
            "contentType": content_type,
            "size": len(file_bytes),
        },
        timeout=settings.DEFAULT_TIMEOUT,
    )

    upload_url = _extract(upload_response, "uploadUrl")
    file_url = _extract(upload_response, "fileUrl")

    if not upload_url or not file_url:
        raise RuntimeError("Could not retrieve JSON2Video upload URL or file URL")

    put_response = requests.put(
        upload_url,
        data=file_bytes,
        headers={"Content-Type": content_type},
        timeout=settings.UPLOAD_TIMEOUT,
    )
    put_response.raise_for_status()

    return str(file_url)


def _upload_video_source(api_key: str, video_bytes: bytes, index: int = 0) -> str:
    return _upload_media_source(api_key, f"clip-{index}.mp4", video_bytes, "video/mp4")


def _apply_visual_adjustments(
    video_element: Dict[str, Any],
    *,
    speed: float,
    rotate: int,
    zoom_level: Optional[float],
    brightness: float,
    contrast: float,
    saturation: float,
    color_preset: Optional[str],
    duck_level: Optional[float],
) -> None:
    if speed != 1.0:
        video_element["speed"] = speed
    if rotate:
        video_element["rotate"] = rotate
    if zoom_level:
        video_element["zoom"] = zoom_level
    if brightness != 1.0:
        video_element["brightness"] = brightness
    if contrast != 1.0:
        video_element["contrast"] = contrast
    if saturation != 1.0:
        video_element["saturation"] = saturation
    if color_preset == "grayscale":
        video_element["grayscale"] = 1
    elif color_preset == "sepia":
        video_element["filter"] = "sepia"
    if duck_level is not None:
        video_element["duck"] = duck_level


def _build_movie_payload(
    clips: List[Dict[str, Any]],
    resolution: str,
    quality: str,
    speed: float,
    rotate: int,
    zoom_level: Optional[float],
    brightness: float,
    contrast: float,
    saturation: float,
    color_preset: Optional[str],
    duck_level: Optional[float],
    transition_type: Optional[str],
    transition_duration: float,
    text_overlays: List[Dict[str, Any]],
    audio_tracks: List[Dict[str, Any]],
    image_overlays: List[Dict[str, Any]],
    voiceover: Optional[Dict[str, Any]] = None,
    subtitles: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not clips:
        raise ValueError("At least one video clip is required")

    scenes: List[Dict[str, Any]] = []
    first_clip_length = None
    for index, clip in enumerate(clips):
        trim_start = clip["trim_start"]
        trim_end = clip["trim_end"]
        if trim_end <= trim_start:
            raise ValueError(f"Trim end must be greater than trim start (clip {index + 1})")

        clip_length = round(trim_end - trim_start, 3)
        if first_clip_length is None:
            first_clip_length = clip_length

        video_element: Dict[str, Any] = {
            "type": "video",
            "src": clip["source_url"],
            "seek": round(trim_start, 3),
            "duration": clip_length,
            "volume": 0 if clip["video_muted"] else clip["video_volume"],
        }
        if clip["video_fade_in"] > 0:
            video_element["fade-in"] = clip["video_fade_in"]
        if clip["video_fade_out"] > 0:
            video_element["fade-out"] = clip["video_fade_out"]

        _apply_visual_adjustments(
            video_element,
            speed=speed,
            rotate=rotate,
            zoom_level=zoom_level,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            color_preset=color_preset,
            duck_level=duck_level,
        )

        scene_elements: List[Dict[str, Any]] = [video_element]

        if index == 0:
            for overlay in text_overlays:
                if not overlay["text"]:
                    continue
                text_element: Dict[str, Any] = {
                    "type": "text",
                    "text": overlay["text"],
                    "style": overlay["style"],
                    "position": overlay["position"],
                    "start": round(overlay["start"], 3),
                    "duration": min(overlay["duration"], clip_length),
                    "font-size": overlay["font_size"],
                    "color": overlay["color"],
                }
                if overlay["font_family"]:
                    text_element["font-family"] = overlay["font_family"]
                if overlay["bg_color"]:
                    text_element["background-color"] = overlay["bg_color"]
                scene_elements.append(text_element)

        scene: Dict[str, Any] = {"elements": scene_elements}
        if transition_type and index < len(clips) - 1:
            scene["transition"] = {"type": transition_type, "duration": transition_duration}
        scenes.append(scene)

    top_level_elements: List[Dict[str, Any]] = []

    for track in audio_tracks:
        if not track["url"]:
            continue
        top_level_elements.append(
            {
                "type": "audio",
                "src": track["url"],
                "volume": track["volume"],
                "fade-in": track["fade_in"],
                "fade-out": track["fade_out"],
                "start": round(track["start"], 3),
            }
        )

    for overlay in image_overlays:
        if not overlay.get("url"):
            continue
        image_element: Dict[str, Any] = {
            "type": "image",
            "src": overlay["url"],
            "position": overlay["position"],
            "opacity": overlay["opacity"],
            "start": round(overlay["start"], 3),
        }
        if overlay["duration"]:
            image_element["duration"] = overlay["duration"]
        top_level_elements.append(image_element)

    if voiceover and voiceover.get("text"):
        voice_element: Dict[str, Any] = {
            "type": "voice",
            "text": voiceover["text"],
            "voice": voiceover["voice"],
        }
        if voiceover.get("model"):
            voice_element["model"] = voiceover["model"]
        top_level_elements.append(voice_element)

    if subtitles:
        subtitles_element: Dict[str, Any] = {"type": "subtitles"}
        if subtitles.get("language"):
            subtitles_element["language"] = subtitles["language"]
        if subtitles.get("model"):
            subtitles_element["model"] = subtitles["model"]
        subtitles_element["settings"] = {
            "style": subtitles["style"],
            "font-size": subtitles["font_size"],
            "position": subtitles["position"],
        }
        top_level_elements.append(subtitles_element)

    payload: Dict[str, Any] = {
        "resolution": resolution,
        "quality": quality,
        "scenes": scenes,
    }
    if top_level_elements:
        payload["elements"] = top_level_elements

    return payload


def fetch_data(
    api_key: str,
    clips: List[Dict[str, Any]],
    resolution: str = "sd",
    quality: str = "medium",
    speed: float = 1.0,
    rotate: int = 0,
    zoom_level: Optional[float] = None,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    color_preset: Optional[str] = None,
    duck_level: Optional[float] = None,
    transition_type: Optional[str] = None,
    transition_duration: float = 1.0,
    text_overlays: Optional[List[Dict[str, Any]]] = None,
    audio_tracks: Optional[List[Dict[str, Any]]] = None,
    image_overlays: Optional[List[Dict[str, Any]]] = None,
    voiceover: Optional[Dict[str, Any]] = None,
    subtitles: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Render a JSON2Video movie and return final video URL details.

    ``clips`` is a list of dicts each containing ``video_bytes``, ``trim_start``, ``trim_end``,
    ``video_volume``, ``video_muted``, ``video_fade_in`` and ``video_fade_out``.
    """
    if not api_key or not api_key.strip():
        raise ValueError("A JSON2Video API key is required")
    if not clips:
        raise ValueError("At least one video clip is required")

    uploaded_clips: List[Dict[str, Any]] = []
    for index, clip in enumerate(clips):
        video_bytes = clip.get("video_bytes")
        if not video_bytes:
            raise ValueError(f"A video file upload is required for clip {index + 1}")
        source_url = _upload_video_source(api_key=api_key, video_bytes=video_bytes, index=index)
        uploaded_clips.append({**clip, "source_url": source_url})

    resolved_text_overlays = text_overlays or []
    resolved_audio_tracks = audio_tracks or []
    resolved_image_overlays: List[Dict[str, Any]] = []
    for overlay in image_overlays or []:
        image_bytes = overlay.get("image_bytes")
        overlay_url = None
        if image_bytes:
            overlay_url = _upload_media_source(api_key, "watermark.png", image_bytes, "image/png")
        resolved_image_overlays.append({**overlay, "url": overlay_url})

    payload = _build_movie_payload(
        clips=uploaded_clips,
        resolution=resolution,
        quality=quality,
        speed=speed,
        rotate=rotate,
        zoom_level=zoom_level,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        color_preset=color_preset,
        duck_level=duck_level,
        transition_type=transition_type,
        transition_duration=transition_duration,
        text_overlays=resolved_text_overlays,
        audio_tracks=resolved_audio_tracks,
        image_overlays=resolved_image_overlays,
        voiceover=voiceover,
        subtitles=subtitles,
    )

    create_response = _request(
        settings.JSON2VIDEO_BASE_URL,
        "POST",
        MOVIE_CREATE_ENDPOINT,
        api_key,
        json_payload=payload,
        timeout=settings.DEFAULT_TIMEOUT * 2,
    )

    project_id = _extract(create_response, "project")
    if not project_id:
        raise RuntimeError("JSON2Video project ID was not returned")

    deadline = time.time() + settings.RENDER_WAIT_TIMEOUT
    while time.time() < deadline:
        status_response = _request(
            settings.JSON2VIDEO_BASE_URL,
            "GET",
            MOVIE_STATUS_ENDPOINT,
            api_key,
            params={"project": project_id},
            timeout=settings.DEFAULT_TIMEOUT,
        )
        status = str(_extract(status_response, "movie.status", "status") or "").lower()

        if status == "done":
            final_url = _render_output_url(status_response)
            if not final_url:
                raise RuntimeError("Render finished but no downloadable video URL was returned")
            return {"status": "done", "url": str(final_url), "render_id": str(project_id)}

        if status == "error":
            message = _extract(status_response, "movie.message", "message") or "JSON2Video render failed"
            return {"status": "failed", "error": str(message), "render_id": str(project_id)}

        time.sleep(settings.POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Timed out waiting for JSON2Video render {project_id}")
