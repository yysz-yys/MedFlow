from sqlalchemy import Column, String, BigInteger, DateTime, func
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class User(Base):
    __tablename__ = "user"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    password = Column(String(255), nullable=False, comment="密码（加密存储）")
    name = Column(String(50), nullable=False, comment="姓名")
    email = Column(String(100), nullable=False, unique=True, comment="邮箱（登录凭证）")
    phone = Column(String(20), unique=True, comment="手机号（选填，填写则唯一）")
    role = Column(TINYINT, nullable=False, comment="角色：0=管理员 / 1=医生 / 2=病人")
    status = Column(TINYINT, nullable=False, default=1, comment="状态：0=禁用 / 1=正常")
    last_login = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
