from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELETED = "deleted"

class PlanCategory(str, Enum):
    PROJECT = "project"
    PERSONAL = "personal"
    LEARNING = "learning"
    BUSINESS = "business"
    CREATIVE = "creative"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"
    CODE = "code"
    DEBUGGING = "debugging"
    BACKEND = "backend"
    FRONTEND = "frontend"
    SYSTEM_DESIGN = "system_design"
    FEATURE_DEVELOPMENT = "feature_development"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(BaseModel):
    id: Optional[int] = None
    plan_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    order_index: int = 0
    dependencies: List[int] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Plan(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: PlanCategory
    goal: str = Field(..., min_length=1, max_length=500)
    status: TaskStatus = TaskStatus.PENDING
    total_tasks: int = 0
    completed_tasks: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tasks: List[Task] = Field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def is_completed(self) -> bool:
        return self.total_tasks > 0 and self.completed_tasks == self.total_tasks

class PlanRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    goal: str = Field(..., min_length=1, max_length=500)
    category: PlanCategory
    description: Optional[str] = Field(None, max_length=1000)
    additional_context: Optional[str] = Field(None, max_length=2000)

class TaskUpdate(BaseModel):
    task_ids: List[int] = Field(..., min_length=1)
    status: TaskStatus
    notes: Optional[str] = Field(None, max_length=500)

class PlanUpdate(BaseModel):
    plan_id: int
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    new_tasks: Optional[List[str]] = None
    task_updates: Optional[List[TaskUpdate]] = None
    additional_context: Optional[str] = Field(None, max_length=1000)
