from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, worker
from app.config import settings
from app.db import Base, engine, get_db
from app.routes_mock import router as mock_router
from app.routes_ops import router as ops_router
from app.schemas import EmployeeIn, EmployeeOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if settings.worker_enabled:
        worker.start()
    yield
    worker.stop()


app = FastAPI(title="ConnectHub", lifespan=lifespan)
app.include_router(mock_router)
app.include_router(ops_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(data: EmployeeIn, db: Session = Depends(get_db)):
    employee = models.Employee(**data.model_dump())
    try:
        db.add(employee)
        db.flush()  # get the id without committing yet
        db.add(
            models.Event(
                type="employee.created",
                payload={"employee_id": employee.id, **data.model_dump()},
            )
        )
        db.commit()  # employee and event are saved together or not at all
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")
    return employee


@app.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return db.scalars(select(models.Employee).order_by(models.Employee.id)).all()


@app.get("/events")
def list_events(db: Session = Depends(get_db)):
    rows = db.scalars(select(models.Event).order_by(models.Event.id)).all()
    return [
        {"id": e.id, "type": e.type, "status": e.status, "payload": e.payload}
        for e in rows
    ]


@app.get("/deliveries")
def list_deliveries(db: Session = Depends(get_db)):
    rows = db.scalars(select(models.Delivery).order_by(models.Delivery.id)).all()
    return [
        {
            "id": d.id,
            "event_id": d.event_id,
            "app": d.app,
            "action": d.action,
            "status": d.status,
            "attempts": d.attempts,
            "last_error": d.last_error,
            "result": d.result,
        }
        for d in rows
    ]


@app.post("/worker/run-once")
def worker_run_once():
    """Run one worker pass by hand (handy for demos and debugging)."""
    return worker.run_once()

