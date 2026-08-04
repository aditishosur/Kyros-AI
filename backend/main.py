from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.bootstrap import init_db
from backend.database import SessionLocal, get_db
from backend.services.analytics import api_analytics, overview, recent_metrics
from backend.services.ml import anomalies, forecast
from backend.services.root_cause import root_cause
from backend.services.simulation import run_simulation

app = FastAPI(title="PulseOps API", version="1.0.0", description="Predictive API operations and performance intelligence.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "pulseops-api"}


@app.get("/apis", response_model=list[schemas.APIOut])
def list_apis(db: Session = Depends(get_db)):
    return db.query(models.API).order_by(models.API.name).all()


@app.get("/apis/{api_id}", response_model=schemas.APIOut)
def get_api(api_id: int, db: Session = Depends(get_db)):
    api = db.query(models.API).filter(models.API.id == api_id).first()
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    return api


@app.post("/apis", response_model=schemas.APIOut, status_code=status.HTTP_201_CREATED)
def create_api(payload: schemas.APICreate, db: Session = Depends(get_db)):
    api = models.API(**payload.model_dump())
    db.add(api)
    db.commit()
    db.refresh(api)
    return api


@app.put("/apis/{api_id}", response_model=schemas.APIOut)
def update_api(api_id: int, payload: schemas.APIUpdate, db: Session = Depends(get_db)):
    api = db.query(models.API).filter(models.API.id == api_id).first()
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(api, key, value)
    db.commit()
    db.refresh(api)
    return api


@app.delete("/apis/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api(api_id: int, db: Session = Depends(get_db)):
    api = db.query(models.API).filter(models.API.id == api_id).first()
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    db.delete(api)
    db.commit()


@app.get("/analytics/overview")
def analytics_overview(db: Session = Depends(get_db)):
    return overview(db)


@app.get("/analytics/apis/{api_id}")
def analytics_api(api_id: int, db: Session = Depends(get_db)):
    data = api_analytics(db, api_id)
    if not data:
        raise HTTPException(status_code=404, detail="API not found")
    return data


@app.get("/analytics/apis/{api_id}/risk")
def analytics_risk(api_id: int, db: Session = Depends(get_db)):
    data = recent_metrics(db, api_id)
    if not data:
        raise HTTPException(status_code=404, detail="API not found")
    return data


@app.get("/analytics/apis/{api_id}/root-cause")
def analytics_root_cause(api_id: int, db: Session = Depends(get_db)):
    data = root_cause(db, api_id)
    if not data:
        raise HTTPException(status_code=404, detail="API not found")
    return data


@app.get("/analytics/apis/{api_id}/anomalies")
def analytics_anomalies(api_id: int, db: Session = Depends(get_db)):
    return anomalies(db, api_id)


@app.get("/predictions/{api_id}")
def predictions(api_id: int, db: Session = Depends(get_db)):
    if not db.query(models.API).filter(models.API.id == api_id).first():
        raise HTTPException(status_code=404, detail="API not found")
    return forecast(db, api_id)


@app.post("/simulation/run", response_model=schemas.SimulationOut)
def simulation(payload: schemas.SimulationIn, db: Session = Depends(get_db)):
    if not db.query(models.API).filter(models.API.id == payload.api_id).first():
        raise HTTPException(status_code=404, detail="API not found")
    return run_simulation(db, payload.api_id, payload.traffic_change, payload.capacity_change, payload.db_latency_change)
