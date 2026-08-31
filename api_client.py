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


def _upload_video_source(api_key: str, video_bytes: bytes) -> str:
    content_type = mimetypes.guess_type("clip.mp4")[0] or "video/mp4"
    upload_response = _request(
        settings.JSON2VIDEO_BASE_URL,
        "POST",
        MEDIA_UPLOAD_ENDPOINT,
        api_key,
        json_payload={
            "name": "clip.mp4",
            "contentType": content_type,
            "size": len(video_bytes),
        },
        timeout=settings.DEFAULT_TIMEOUT,
    )

    upload_url = _extract(upload_response, "uploadUrl")
    file_url = _extract(upload_response, "fileUrl")

    if not upload_url or not file_url:
        raise RuntimeError("Could not retrieve JSON2Video upload URL or file URL")

    put_response = requests.put(
        upload_url,
        data=video_bytes,
        headers={"Content-Type": content_type},
        timeout=settings.UPLOAD_TIMEOUT,
    )
    put_response.raise_for_status()

    return str(file_url)


def _build_movie_payload(
    source_url: str,
    trim_start: float,
    trim_end: float,
    text_overlay: str,
    music_url: Optional[str],
) -> Dict[str, Any]:
    if trim_end <= trim_start:
        raise ValueError("Trim end must be greater than trim start")

    clip_length = round(trim_end - trim_start, 3)

    video_element: Dict[str, Any] = {
        "type": "video",
        "src": source_url,
        "seek": round(trim_start, 3),
        "duration": clip_length,
    }

    elements = [video_element]

    if text_overlay:
        elements.append(
            {
                "type": "text",
                "text": text_overlay,
                "style": "minimal",
                "position": "bottom-center",
                "duration": min(clip_length, 5),
            }
        )

    if music_url:
        elements.append(
            {
                "type": "audio",
                "src": music_url,
                "duration": clip_length,
                "volume": 0.4,
                "fade-in": 1,
                "fade-out": 1,
            }
        )

    return {
        "resolution": "sd",
        "quality": "medium",
        "scenes": [{"elements": elements}],
    }


def fetch_data(
    api_key: str,
    video_bytes: bytes,
    trim_start: float,
    trim_end: float,
    text_overlay: str = "",
    music_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Render a JSON2Video movie and return final video URL details."""
    if not api_key or not api_key.strip():
        raise ValueError("A JSON2Video API key is required")
    if not video_bytes:
        raise ValueError("A video file upload is required")

    source_url = _upload_video_source(api_key=api_key, video_bytes=video_bytes)

    payload = _build_movie_payload(
        source_url=source_url,
        trim_start=trim_start,
        trim_end=trim_end,
        text_overlay=text_overlay,
        music_url=music_url,
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
