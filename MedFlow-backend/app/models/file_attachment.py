from sqlalchemy import func, Column, String, BigInteger, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class FileAttachment(Base):
    __tablename__ = "file_attachment"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    uploader_id = Column(BigInteger, nullable=False, comment="上传人ID")
    uploader_role = Column(TINYINT, nullable=False, comment="上传人角色（取值同user_role字典）")
    related_type = Column(String(50), nullable=False, comment="关联对象类型")
    related_id = Column(BigInteger, nullable=False, comment="关联对象ID")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="存储路径")
    file_size = Column(BigInteger, comment="文件大小(字节)")
    file_type = Column(String(100), comment="MIME类型")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="上传时间")
