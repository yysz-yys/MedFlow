import os
import uuid
import filetype
from datetime import datetime
from fastapi import UploadFile
from app.core.config import get_settings

settings = get_settings()
ALLOWED_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4", "video/x-msvideo", "video/quicktime"}


async def save_upload(file: UploadFile) -> dict:
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"文件大小超过 {settings.MAX_FILE_SIZE_MB}MB 限制")

    kind = filetype.guess(contents)
    if kind is None or kind.mime not in ALLOWED_MIMES:
        raise ValueError("仅支持图片(jpg/png/gif/webp)和视频(mp4/avi/mov)")

    date_dir = datetime.now().strftime("%Y/%m/%d")
    dir_path = os.path.join(settings.UPLOAD_DIR, date_dir)
    os.makedirs(dir_path, exist_ok=True)

    ext = kind.extension
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(dir_path, stored_name)

    with open(stored_path, "wb") as f:
        f.write(contents)

    return {
        "file_name": file.filename,
        "file_path": os.path.join(date_dir, stored_name),
        "file_size": len(contents),
        "file_type": kind.mime,
    }
