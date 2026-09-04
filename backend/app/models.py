"""
SQLAlchemy ORM Models for Surveys, Detections, and Navigation Pings.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    image_path = Column(String(512), nullable=False)
    image_width = Column(Integer, default=0)
    image_height = Column(Integer, default=0)
    metadata_path = Column(String(512), nullable=True)
    status = Column(String(32), default="uploaded", index=True)  # uploaded, processing, done, failed
    error_message = Column(Text, nullable=True)
    
    total_detections = Column(Integer, default=0)
    high_tier_count = Column(Integer, default=0)
    medium_tier_count = Column(Integer, default=0)
    low_tier_count = Column(Integer, default=0)
    
    nadir_x = Column(Integer, nullable=True)
    slant_range_m = Column(Float, default=75.0)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    detections = relationship("Detection", back_populates="survey", cascade="all, delete-orphan")
    pings = relationship("PingRecord", back_populates="survey", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(String(64), primary_key=True, index=True)
    survey_id = Column(String(64), ForeignKey("surveys.id", ondelete="CASCADE"), index=True)
    ping_index = Column(Integer, default=0)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    depth_m = Column(Float, nullable=True)
    
    bbox_x = Column(Integer, nullable=False)
    bbox_y = Column(Integer, nullable=False)
    bbox_width = Column(Integer, nullable=False)
    bbox_height = Column(Integer, nullable=False)
    estimated_size_m = Column(String(64), default="Unknown")
    
    predicted_class = Column(String(64), nullable=False)  # ghost_net, pipe_cylinder, shipwreck_fragment
    confidence_score = Column(Float, nullable=False)      # 0.0 to 100.0
    confidence_tier = Column(String(16), nullable=False)  # High, Medium, Low
    
    detector_score = Column(Float, default=0.0)
    shadow_score = Column(Float, default=0.0)
    shape_score = Column(Float, default=0.0)
    shadow_detected = Column(Boolean, default=False)
    
    thumbnail_url = Column(String(512), nullable=True)
    timestamp = Column(String(64), nullable=False)
    filter_details_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)

    survey = relationship("Survey", back_populates="detections")

    @property
    def detection_id(self):
        return self.id

    @property
    def bbox(self):
        return [self.bbox_x, self.bbox_y, self.bbox_width, self.bbox_height]

    @property
    def filter_details(self):
        if self.filter_details_json:
            try:
                return json.loads(self.filter_details_json)
            except Exception:
                return {}
        return {}


class PingRecord(Base):
    __tablename__ = "ping_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(String(64), ForeignKey("surveys.id", ondelete="CASCADE"), index=True)
    ping_index = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    depth_m = Column(Float, nullable=True)
    heading_deg = Column(Float, nullable=True)
    timestamp = Column(String(64), nullable=False)

    survey = relationship("Survey", back_populates="pings")
