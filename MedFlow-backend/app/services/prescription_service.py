import json
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.models.drug import Drug
from app.models.drug_order import DrugOrder
from app.models.diagnosis_record import DiagnosisRecord
from app.models.doctor import Doctor
from app.models.patient import Patient
from decimal import Decimal

async def create_prescription(db: AsyncSession, diagnosis_id: int, doctor_id: int,
                               items: list[dict]):
    diag = (await db.execute(select(DiagnosisRecord).where(
        DiagnosisRecord.id == diagnosis_id))).scalar_one_or_none()
    if diag is None: raise HTTPException(status_code=404, detail="诊断记录不存在")
    if diag.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="只能为自己诊断开处方")

    existing = (await db.execute(select(Prescription).where(
        Prescription.diagnosis_id == diagnosis_id))).scalar_one_or_none()
    if existing: raise HTTPException(status_code=400, detail="该诊断已有处方")

    prescription = Prescription(diagnosis_id=diagnosis_id, doctor_id=doctor_id,
                                patient_id=diag.patient_id)
    db.add(prescription)
    await db.flush()

    total_amount = Decimal("0")
    new_value_items = []
    for item in items:
        drug = (await db.execute(select(Drug).where(
            Drug.id == item["drug_id"], Drug.deleted_at.is_(None)))).scalar_one_or_none()
        if drug is None: raise HTTPException(status_code=400, detail=f"药品 {item['drug_id']} 不存在")
        qty = item["quantity"]
        if drug.stock < qty: raise HTTPException(status_code=400, detail=f"药品 {drug.name} 库存不足")
        drug.stock -= qty

        pi = PrescriptionItem(prescription_id=prescription.id, drug_id=drug.id,
                              quantity=qty, usage_method=item.get("usage_method"),
                              days=item.get("days"))
        db.add(pi)
        total_amount += drug.price * qty
        new_value_items.append({"drug_id": drug.id, "drug_name": drug.name, "quantity": qty})

    order = DrugOrder(prescription_id=prescription.id, total_amount=total_amount)
    db.add(order)
    await db.flush()

    pt = (await db.execute(select(Patient).where(Patient.id == diag.patient_id))).scalar_one()
    from app.services.notification_service import create_notification
    await create_notification(db, pt.user_id, "处方已生成",
        f"您的药品订单已生成，总金额 {total_amount} 元", "DISPENSE", "drug_order", order.id)

    return {"prescription_id": prescription.id, "order_id": order.id,
            "new_value": json.dumps(new_value_items)}

async def update_prescription(db: AsyncSession, prescription_id: int, doctor_id: int,
                               items: list[dict]):
    prescription = (await db.execute(select(Prescription).where(
        Prescription.id == prescription_id))).scalar_one_or_none()
    if prescription is None: raise HTTPException(status_code=404, detail="处方不存在")
    if prescription.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="无权修改他人处方")

    order = (await db.execute(select(DrugOrder).where(
        DrugOrder.prescription_id == prescription_id))).scalar_one_or_none()
    if order and order.status == 2:
        raise HTTPException(status_code=400, detail="药品已取药，处方不可修改")

    old_items = (await db.execute(select(PrescriptionItem).where(
        PrescriptionItem.prescription_id == prescription_id))).scalars().all()
    old_value_items = []
    for oi in old_items:
        drug = (await db.execute(select(Drug).where(Drug.id == oi.drug_id))).scalar_one()
        drug.stock += oi.quantity
        old_value_items.append({"drug_id": oi.drug_id, "drug_name": drug.name, "quantity": oi.quantity})
    for oi in old_items:
        await db.delete(oi)

    total_amount = Decimal("0")
    new_value_items = []
    for item in items:
        drug = (await db.execute(select(Drug).where(
            Drug.id == item["drug_id"], Drug.deleted_at.is_(None)))).scalar_one_or_none()
        if drug is None or drug.stock < item["quantity"]:
            raise HTTPException(status_code=400, detail=f"药品 {item['drug_id']} 不可用")
        drug.stock -= item["quantity"]
        pi = PrescriptionItem(prescription_id=prescription_id, drug_id=drug.id,
                              quantity=item["quantity"],
                              usage_method=item.get("usage_method"), days=item.get("days"))
        db.add(pi)
        total_amount += drug.price * item["quantity"]
        new_value_items.append({"drug_id": drug.id, "drug_name": drug.name, "quantity": item["quantity"]})

    if order: order.total_amount = total_amount
    return {"old_value": json.dumps(old_value_items), "new_value": json.dumps(new_value_items)}
