from datetime import date as date_type, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db; from app.core.deps import require_role, get_current_user
from app.models.drug_order import DrugOrder
from app.models.prescription import Prescription
from app.models.doctor import Doctor; from app.models.patient import Patient
from app.schemas.drug_order import DrugOrderOut
from app.services.drug_order_service import cancel_order, complete_order, uncomplete_order, restore_order

router = APIRouter(prefix="/drug-orders", tags=["药品订单"])

async def _check_order_owner(order_id: int, current_user, db):
    """返回订单 ORM 对象，校验当前用户是否有权操作该订单"""
    result = await db.execute(
        select(DrugOrder).options(
            joinedload(DrugOrder.prescription).joinedload(Prescription.patient),
            joinedload(DrugOrder.prescription).joinedload(Prescription.doctor),
        ).where(DrugOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if current_user.role == 0:
        return order
    if current_user.role == 1:
        doctor = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
        if doctor and order.prescription.doctor_id == doctor.id:
            return order
    else:
        patient = (await db.execute(select(Patient).where(Patient.user_id == current_user.id))).scalar_one_or_none()
        if patient and order.prescription.patient_id == patient.id:
            return order
    raise HTTPException(status_code=403, detail="无权操作该订单")


@router.get("", response_model=list[DrugOrderOut])
async def list_orders(
    date: date_type = None,
    status: int = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DrugOrder).options(
        joinedload(DrugOrder.prescription).joinedload(Prescription.doctor).joinedload(Doctor.user),
        joinedload(DrugOrder.prescription).joinedload(Prescription.patient).joinedload(Patient.user)
    )
    if current_user.role == 0: pass
    elif current_user.role == 1:
        doctor = (await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))).scalar_one_or_none()
        if doctor: query = query.where(DrugOrder.prescription.has(Prescription.doctor_id == doctor.id))
        else: return []
    else:
        patient = (await db.execute(select(Patient).where(Patient.user_id == current_user.id))).scalar_one_or_none()
        if patient: query = query.where(DrugOrder.prescription.has(Prescription.patient_id == patient.id))
        else: return []

    if date:
        start = datetime.combine(date, datetime.min.time())
        end = start + timedelta(days=1)
        query = query.where(DrugOrder.created_at >= start, DrugOrder.created_at < end)
    if status is not None:
        query = query.where(DrugOrder.status == status)

    orders = (await db.execute(query.order_by(DrugOrder.created_at.desc()))).scalars().all()
    result = []
    for o in orders:
        try:
            patient_name = o.prescription.patient.user.name if o.prescription and o.prescription.patient and o.prescription.patient.user else '未知'
            doctor_name = o.prescription.doctor.user.name if o.prescription and o.prescription.doctor and o.prescription.doctor.user else '未知'
        except Exception:
            patient_name = '未知'
            doctor_name = '未知'
        result.append(DrugOrderOut(id=o.id, prescription_id=o.prescription_id,
            total_amount=o.total_amount, status=o.status,
            patient_name=patient_name, doctor_name=doctor_name,
            created_at=o.created_at.isoformat() if o.created_at else None))
    return result


@router.post("/{order_id}/cancel")
async def cancel(order_id: int, current_user=Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    """病人取消自己的订单，退还库存"""
    await _check_order_owner(order_id, current_user, db)
    await cancel_order(db, order_id)
    return {"message": "订单已取消，库存已退还"}


@router.post("/{order_id}/complete")
async def complete(order_id: int, current_user=Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    """病人确认取药完成"""
    if current_user.role not in (0, 2):
        raise HTTPException(status_code=403, detail="仅病人和管理员可标记取药完成")
    await _check_order_owner(order_id, current_user, db)
    await complete_order(db, order_id)
    return {"message": "订单已完成"}

@router.post("/{order_id}/uncomplete")
async def uncomplete(order_id: int, current_user=Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    """病人撤回取药确认"""
    if current_user.role not in (0, 2):
        raise HTTPException(status_code=403, detail="仅病人和管理员可撤回")
    await _check_order_owner(order_id, current_user, db)
    await uncomplete_order(db, order_id)
    return {"message": "已撤回取药确认"}

@router.post("/{order_id}/restore")
async def restore(order_id: int, current_user=Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    """病人恢复已取消的订单"""
    if current_user.role not in (0, 2):
        raise HTTPException(status_code=403, detail="仅病人和管理员可恢复")
    await _check_order_owner(order_id, current_user, db)
    await restore_order(db, order_id)
    return {"message": "订单已恢复"}
