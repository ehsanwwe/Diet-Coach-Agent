"""
Local audio file storage service.

Files are stored under AUDIO_STORAGE_PATH (default: ./storage/audio).
Filenames are UUID-based to avoid collisions and path traversal.
Absolute filesystem paths are never returned to callers — use storage_key instead.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from app.core.config import settings


def _storage_root() -> Path:
    return Path(settings.AUDIO_STORAGE_PATH).resolve()


def _ensure_dir() -> Path:
    root = _storage_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _extension_for_mime(mime_type: str | None) -> str:
    mapping = {
        "audio/webm": ".webm",
        "audio/webm;codecs=opus": ".webm",
        "audio/ogg": ".ogg",
        "audio/ogg;codecs=opus": ".ogg",
        "audio/mp4": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
    }
    if mime_type:
        base = mime_type.split(";")[0].strip().lower()
        return mapping.get(mime_type.lower(), mapping.get(base, ".bin"))
    return ".bin"


def save_audio_file(data: bytes, mime_type: str | None) -> tuple[str, str]:
    """
    Persist audio bytes to disk.

    Returns (storage_key, absolute_path).
    storage_key is a relative path under AUDIO_STORAGE_PATH — safe to store in DB.
    absolute_path is the real on-disk path — used only during the upload request.
    """
    root = _ensure_dir()
    ext = _extension_for_mime(mime_type)
    filename = f"{uuid.uuid4().hex}{ext}"
    abs_path = root / filename
    abs_path.write_bytes(data)
    return filename, str(abs_path)


def delete_audio_file(storage_key: str) -> None:
    root = _storage_root()
    target = root / storage_key
    try:
        target.unlink(missing_ok=True)
    except OSError:
        pass


def validate_upload(
    data: bytes,
    mime_type: str | None,
) -> str | None:
    """
    Return an error message string if the upload is invalid, else None.
    """
    max_bytes = settings.MAX_AUDIO_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        return f"File exceeds maximum size of {settings.MAX_AUDIO_UPLOAD_MB} MB"

    if mime_type:
        base_mime = mime_type.split(";")[0].strip().lower()
        allowed = [m.split(";")[0].strip().lower() for m in settings.allowed_audio_mime_types_list]
        if base_mime not in allowed:
            return f"Unsupported audio format: {mime_type}"

    return None
