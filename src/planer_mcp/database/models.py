from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class PlanModel(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    goal = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    tasks = relationship("TaskModel", back_populates="plan", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_plans_category', 'category'),
        Index('idx_plans_updated_at', 'updated_at'),
    )

class TaskModel(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    priority = Column(String(50), default="medium")
    order_index = Column(Integer, default=0)
    dependencies = Column(Text, default="[]")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    plan = relationship("PlanModel", back_populates="tasks")
    
    __table_args__ = (
        Index('idx_tasks_plan_id', 'plan_id'),
        Index('idx_tasks_status', 'status'),
    )
