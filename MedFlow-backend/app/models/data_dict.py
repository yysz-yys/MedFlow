from sqlalchemy import func, Column, String, BigInteger, Integer, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base

class DataDict(Base):
    __tablename__ = "data_dict"
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    dict_type = Column(String(50), nullable=False, comment="字典类型")
    dict_key = Column(TINYINT, nullable=False, comment="枚举值")
    dict_label = Column(String(50), nullable=False, comment="显示文本")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="修改时间")
