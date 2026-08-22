from app.utils.file_upload import save_upload
from app.models.file_attachment import FileAttachment


async def upload_file(db, uploader_id: int, uploader_role: int,
                       related_type: str, related_id: int, file):
    info = await save_upload(file)
    attachment = FileAttachment(
        uploader_id=uploader_id, uploader_role=uploader_role,
        related_type=related_type, related_id=related_id,
        file_name=info["file_name"], file_path=info["file_path"],
        file_size=info["file_size"], file_type=info["file_type"],
    )
    db.add(attachment)
    await db.flush()
    return attachment
