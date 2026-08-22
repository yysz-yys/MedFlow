from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.drug_order import DrugOrder
from app.models.prescription_item import PrescriptionItem
from app.models.drug import Drug

async def cancel_order(db: AsyncSession, order_id: int):
    order = (await db.execute(select(DrugOrder).where(DrugOrder.id == order_id))).scalar_one_or_none()
    if order is None: raise HTTPException(status_code=404, detail="订单不存在")
    order.status = 0
    items = (await db.execute(select(PrescriptionItem).where(
        PrescriptionItem.prescription_id == order.prescription_id))).scalars().all()
    for item in items:
        drug = (await db.execute(select(Drug).where(Drug.id == item.drug_id))).scalar_one()
        drug.stock += item.quantity
    return order


async def complete_order(db: AsyncSession, order_id: int):
    order = (await db.execute(select(DrugOrder).where(DrugOrder.id == order_id))).scalar_one_or_none()
    if order is None: raise HTTPException(status_code=404, detail="订单不存在")
    order.status = 2
    return order

async def uncomplete_order(db: AsyncSession, order_id: int):
    order = (await db.execute(select(DrugOrder).where(DrugOrder.id == order_id))).scalar_one_or_none()
    if order is None: raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != 2:
        raise HTTPException(status_code=400, detail="仅已取药状态可撤回")
    order.status = 1
    return order

async def restore_order(db: AsyncSession, order_id: int):
    order = (await db.execute(select(DrugOrder).where(DrugOrder.id == order_id))).scalar_one_or_none()
    if order is None: raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != 0:
        raise HTTPException(status_code=400, detail="仅已取消状态可恢复")
    items = (await db.execute(select(PrescriptionItem).where(
        PrescriptionItem.prescription_id == order.prescription_id))).scalars().all()
    for item in items:
        drug = (await db.execute(select(Drug).where(Drug.id == item.drug_id))).scalar_one()
        if drug.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"「{drug.name}」库存不足，无法恢复")
        drug.stock -= item.quantity
    order.status = 1
    return order
