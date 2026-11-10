from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import alerts, circuit, models
from app.db import get_db
from app.models import utcnow

router = APIRouter(tags=["operations"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    counts = dict(
        db.execute(
            select(models.Delivery.status, func.count()).group_by(models.Delivery.status)
        ).all()
    )
    oldest = db.scalar(
        select(func.min(models.Delivery.run_at)).where(models.Delivery.status == "pending")
    )
    apps = db.scalars(select(models.AppState).order_by(models.AppState.app)).all()
    return {
        "deliveries": counts,
        "oldest_pending_age_s": round((utcnow() - oldest).total_seconds(), 1) if oldest else 0,
        "apps": [
            {
                "app": a.app,
                "state": "paused" if circuit.is_paused(a) else "active",
                "consecutive_failures": a.consecutive_failures,
                "paused_until": a.paused_until,
            }
            for a in apps
        ],
        "recent_alerts": list(alerts.recent)[-10:],
    }


@router.post("/deliveries/{delivery_id}/retry")
def retry_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """Give a dead delivery a fresh start."""
    d = db.get(models.Delivery, delivery_id)
    if d is None:
        raise HTTPException(404, "No such delivery")
    if d.status != "dead":
        raise HTTPException(409, "Only dead deliveries can be retried")
    d.status = "pending"
    d.attempts = 0
    d.run_at = utcnow()
    db.commit()
    return {"id": d.id, "status": d.status}
