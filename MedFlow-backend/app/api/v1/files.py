import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db; from app.core.deps import get_current_user
from app.core.config import get_settings
from app.models.file_attachment import FileAttachment
from app.services.file_service import upload_file

router = APIRouter(prefix="/files", tags=["文件"])
settings = get_settings()


@router.post("/upload")
async def upload(related_type: str = Form(...), related_id: int = Form(...),
                 file: UploadFile = File(...), current_user=Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    attachment = await upload_file(db, current_user.id, current_user.role,
                                    related_type, related_id, file)
    return {"id": attachment.id, "file_name": attachment.file_name}


@router.get("/{file_id}/download")
async def download(file_id: int, current_user=Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    fa = (await db.execute(select(FileAttachment).where(
        FileAttachment.id == file_id))).scalar_one_or_none()
    if fa is None: raise HTTPException(status_code=404, detail="文件不存在")
    full_path = os.path.join(settings.UPLOAD_DIR, fa.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(full_path, filename=fa.file_name)


@router.delete("/{file_id}")
async def remove(file_id: int, current_user=Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    fa = (await db.execute(select(FileAttachment).where(
        FileAttachment.id == file_id))).scalar_one_or_none()
    if fa is None: raise HTTPException(status_code=404)
    if current_user.id != fa.uploader_id and current_user.role != 0:
        raise HTTPException(status_code=403)
    full_path = os.path.join(settings.UPLOAD_DIR, fa.file_path)
    if os.path.exists(full_path): os.remove(full_path)
    await db.delete(fa)
    return {"message": "已删除"}
