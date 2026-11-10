from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.db import Base, engine, get_db
from app.schemas import EmployeeIn, EmployeeOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="ConnectHub", lifespan=lifespan)


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
