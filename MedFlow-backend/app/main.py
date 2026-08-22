from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.departments import router as departments_router
from app.api.v1.doctors import router as doctors_router
from app.api.v1.doctor_schedules import router as doctor_schedules_router
from app.api.v1.patients import router as patients_router
from app.api.v1.drugs import router as drugs_router
from app.api.v1.files import router as files_router
from app.api.v1.diagnosis_records import router as diagnosis_records_router
from app.api.v1.system_config import router as system_config_router
from app.api.v1.data_dict import router as data_dict_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.prescriptions import router as prescriptions_router
from app.api.v1.drug_orders import router as drug_orders_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.middleware.auth import AuthMiddleware
from app.middleware.audit import AuditMiddleware
from app.utils.exceptions import app_exception_handler, global_exception_handler, AppException
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="云诊易 MedFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(AuditMiddleware)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(doctor_schedules_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(drugs_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(diagnosis_records_router, prefix="/api/v1")
app.include_router(system_config_router, prefix="/api/v1")
app.include_router(data_dict_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")
app.include_router(drug_orders_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(audit_logs_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    from app.core.sysconfig import load_sysconfig
    await load_sysconfig()
    from tasks.scheduler import start_scheduler
    from app.core.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    start_scheduler()


@app.get("/")
async def root():
    return {"message": "云诊易 MedFlow API"}
