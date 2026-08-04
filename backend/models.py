from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class API(Base):
    __tablename__ = "apis"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    endpoint = Column(String(255), nullable=False, unique=True)
    method = Column(String(12), nullable=False, default="GET")
    owner = Column(String(120), nullable=False, default="Platform")
    description = Column(Text, nullable=False, default="")
    status = Column(String(40), nullable=False, default="Healthy")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    logs = relationship("APILog", back_populates="api", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="api", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="api", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="api", cascade="all, delete-orphan")


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    request_count = Column(Integer, nullable=False)
    cpu_usage = Column(Float, nullable=False)
    db_latency_ms = Column(Float, nullable=False)

    api = relationship("API", back_populates="logs")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    predicted_request_count = Column(Float, nullable=False)
    predicted_latency = Column(Float, nullable=False)
    predicted_error_rate = Column(Float, nullable=False)
    predicted_risk = Column(Float, nullable=False)

    api = relationship("API", back_populates="predictions")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False, index=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    severity = Column(String(40), nullable=False)
    root_cause = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    api = relationship("API", back_populates="incidents")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False, index=True)
    traffic_change = Column(Float, nullable=False)
    capacity_change = Column(Float, nullable=False)
    db_latency_change = Column(Float, nullable=False)
    predicted_latency = Column(Float, nullable=False)
    predicted_error_rate = Column(Float, nullable=False)
    predicted_risk = Column(Float, nullable=False)
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    api = relationship("API", back_populates="simulations")

