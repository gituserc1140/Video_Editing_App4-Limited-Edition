from __future__ import annotations

import mimetypes
import time
from typing import Any, Dict, Optional
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


def _upload_video_source(api_key: str, video_bytes: bytes) -> str:
    return _upload_media_source(api_key, "clip.mp4", video_bytes, "video/mp4")


def _build_movie_payload(
    source_url: str,
    trim_start: float,
    trim_end: float,
    resolution: str,
    quality: str,
    video_volume: float,
    video_muted: bool,
    video_fade_in: float,
    video_fade_out: float,
    text_overlay: str,
    font_family: Optional[str],
    font_size: int,
    text_color: str,
    text_bg_color: Optional[str],
    text_position: str,
    text_style: str,
    music_url: Optional[str],
    music_volume: float,
    music_fade_in: float,
    music_fade_out: float,
    music_start: float,
    watermark_url: Optional[str],
    watermark_position: str,
    watermark_opacity: float,
) -> Dict[str, Any]:
    if trim_end <= trim_start:
        raise ValueError("Trim end must be greater than trim start")

    clip_length = round(trim_end - trim_start, 3)

    video_element: Dict[str, Any] = {
        "type": "video",
        "src": source_url,
        "seek": round(trim_start, 3),
        "duration": clip_length,
        "volume": 0 if video_muted else video_volume,
    }
    if video_fade_in > 0:
        video_element["fade-in"] = video_fade_in
    if video_fade_out > 0:
        video_element["fade-out"] = video_fade_out

    elements = [video_element]

    if text_overlay:
        text_element: Dict[str, Any] = {
            "type": "text",
            "text": text_overlay,
            "style": text_style,
            "position": text_position,
            "duration": min(clip_length, 5),
            "font-size": font_size,
            "color": text_color,
        }
        if font_family:
            text_element["font-family"] = font_family
        if text_bg_color:
            text_element["background-color"] = text_bg_color
        elements.append(text_element)

    if music_url:
        elements.append(
            {
                "type": "audio",
                "src": music_url,
                "duration": clip_length,
                "volume": music_volume,
                "fade-in": music_fade_in,
                "fade-out": music_fade_out,
                "start": round(music_start, 3),
            }
        )

    if watermark_url:
        elements.append(
            {
                "type": "image",
                "src": watermark_url,
                "duration": clip_length,
                "position": watermark_position,
                "opacity": watermark_opacity,
            }
        )

    return {
        "resolution": resolution,
        "quality": quality,
        "scenes": [{"elements": elements}],
    }


def fetch_data(
    api_key: str,
    video_bytes: bytes,
    trim_start: float,
    trim_end: float,
    resolution: str = "sd",
    quality: str = "medium",
    video_volume: float = 1.0,
    video_muted: bool = False,
    video_fade_in: float = 0.0,
    video_fade_out: float = 0.0,
    text_overlay: str = "",
    font_family: Optional[str] = None,
    font_size: int = 32,
    text_color: str = "#FFFFFF",
    text_bg_color: Optional[str] = None,
    text_position: str = "bottom-center",
    text_style: str = "minimal",
    music_url: Optional[str] = None,
    music_volume: float = 0.4,
    music_fade_in: float = 1.0,
    music_fade_out: float = 1.0,
    music_start: float = 0.0,
    watermark_bytes: Optional[bytes] = None,
    watermark_position: str = "bottom-right",
    watermark_opacity: float = 1.0,
) -> Dict[str, Any]:
    """Render a JSON2Video movie and return final video URL details."""
    if not api_key or not api_key.strip():
        raise ValueError("A JSON2Video API key is required")
    if not video_bytes:
        raise ValueError("A video file upload is required")

    source_url = _upload_video_source(api_key=api_key, video_bytes=video_bytes)

    watermark_url = None
    if watermark_bytes:
        watermark_url = _upload_media_source(api_key, "watermark.png", watermark_bytes, "image/png")

    payload = _build_movie_payload(
        source_url=source_url,
        trim_start=trim_start,
        trim_end=trim_end,
        resolution=resolution,
        quality=quality,
        video_volume=video_volume,
        video_muted=video_muted,
        video_fade_in=video_fade_in,
        video_fade_out=video_fade_out,
        text_overlay=text_overlay,
        font_family=font_family,
        font_size=font_size,
        text_color=text_color,
        text_bg_color=text_bg_color,
        text_position=text_position,
        text_style=text_style,
        music_url=music_url,
        music_volume=music_volume,
        music_fade_in=music_fade_in,
        music_fade_out=music_fade_out,
        music_start=music_start,
        watermark_url=watermark_url,
        watermark_position=watermark_position,
        watermark_opacity=watermark_opacity,
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
