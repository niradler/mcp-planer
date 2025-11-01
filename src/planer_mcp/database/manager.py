from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

from sqlalchemy import create_engine, case
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from .models import Base, PlanModel, TaskModel
from ..models.schemas import Plan, Task, TaskStatus, PlanCategory, Priority

class DatabaseManager:
    def __init__(self, db_path: str = "plans.db") -> None:
        self.db_path = Path(db_path)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _get_session(self) -> Session:
        return self.SessionLocal()
    
    def create_plan(self, plan: Plan) -> Plan:
        session = self._get_session()
        try:
            plan_model = PlanModel(
                title=plan.title,
                description=plan.description,
                category=plan.category.value,
                goal=plan.goal,
                status=plan.status.value,
                total_tasks=len(plan.tasks)
            )
            session.add(plan_model)
            session.flush()
            
            created_tasks = []
            for i, task in enumerate(plan.tasks):
                task_model = TaskModel(
                    plan_id=plan_model.id,
                    title=task.title,
                    description=task.description,
                    status=task.status.value,
                    priority=task.priority.value,
                    order_index=i,
                    dependencies=json.dumps(task.dependencies)
                )
                session.add(task_model)
                session.flush()
                
                task.id = task_model.id
                task.plan_id = plan_model.id
                task.created_at = task_model.created_at
                task.updated_at = task_model.updated_at
                created_tasks.append(task)
            
            session.commit()
            session.refresh(plan_model)
            
            plan.id = plan_model.id
            plan.created_at = plan_model.created_at
            plan.updated_at = plan_model.updated_at
            plan.total_tasks = plan_model.total_tasks
            plan.completed_tasks = plan_model.completed_tasks
            plan.tasks = created_tasks
            
            return plan
        finally:
            session.close()
    
    def get_plan(self, plan_id: int) -> Optional[Plan]:
        session = self._get_session()
        try:
            plan_model = session.query(PlanModel).filter(PlanModel.id == plan_id).first()
            if not plan_model:
                return None
            
            task_models = session.query(TaskModel).filter(
                TaskModel.plan_id == plan_id
            ).order_by(TaskModel.order_index).all()
            
            tasks = []
            for task_model in task_models:
                tasks.append(Task(
                    id=task_model.id,
                    plan_id=task_model.plan_id,
                    title=task_model.title,
                    description=task_model.description,
                    status=TaskStatus(task_model.status),
                    priority=Priority(task_model.priority),
                    order_index=task_model.order_index,
                    dependencies=json.loads(task_model.dependencies) if task_model.dependencies else [],
                    created_at=task_model.created_at,
                    updated_at=task_model.updated_at,
                    completed_at=task_model.completed_at
                ))
            
            return Plan(
                id=plan_model.id,
                title=plan_model.title,
                description=plan_model.description,
                category=PlanCategory(plan_model.category),
                goal=plan_model.goal,
                status=TaskStatus(plan_model.status),
                total_tasks=plan_model.total_tasks,
                completed_tasks=plan_model.completed_tasks,
                created_at=plan_model.created_at,
                updated_at=plan_model.updated_at,
                tasks=tasks
            )
        finally:
            session.close()
    
    def get_all_plans(self, include_completed: bool = False, page: int = 1, page_size: int = 30) -> List[Plan]:
        session = self._get_session()
        try:
            query = session.query(PlanModel)
            
            if not include_completed:
                query = query.filter(
                    (PlanModel.total_tasks == 0) | 
                    (PlanModel.completed_tasks < PlanModel.total_tasks)
                )
            
            query = query.order_by(PlanModel.updated_at.desc())
            
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            plan_models = query.all()
            
            plans = []
            for plan_model in plan_models:
                plans.append(Plan(
                    id=plan_model.id,
                    title=plan_model.title,
                    description=plan_model.description,
                    category=PlanCategory(plan_model.category),
                    goal=plan_model.goal,
                    status=TaskStatus(plan_model.status),
                    total_tasks=plan_model.total_tasks,
                    completed_tasks=plan_model.completed_tasks,
                    created_at=plan_model.created_at,
                    updated_at=plan_model.updated_at,
                    tasks=[]
                ))
            
            return plans
        finally:
            session.close()
    
    def update_task_status(self, task_ids: List[int], status: TaskStatus, notes: Optional[str] = None) -> bool:
        session = self._get_session()
        try:
            update_time = datetime.now()
            completed_time = update_time if status == TaskStatus.COMPLETED else None
            
            affected_tasks = session.query(TaskModel).filter(TaskModel.id.in_(task_ids)).all()
            if not affected_tasks:
                return False
            
            for task in affected_tasks:
                task.status = status.value
                task.updated_at = update_time
                if completed_time:
                    task.completed_at = completed_time
            
            affected_plan_ids = set(task.plan_id for task in affected_tasks)
            
            for plan_id in affected_plan_ids:
                self._update_plan_progress(session, plan_id)
            
            session.commit()
            return True
        finally:
            session.close()
    
    def _update_plan_progress(self, session: Session, plan_id: int) -> None:
        result = session.query(
            func.count(TaskModel.id).label('total'),
            func.sum(case((TaskModel.status == 'completed', 1), else_=0)).label('completed')
        ).filter(
            TaskModel.plan_id == plan_id,
            TaskModel.status != 'deleted'
        ).first()
        
        total = result.total or 0
        completed = result.completed or 0
        
        plan = session.query(PlanModel).filter(PlanModel.id == plan_id).first()
        if plan:
            plan.total_tasks = total
            plan.completed_tasks = completed
            plan.updated_at = datetime.now()
    
    def add_tasks_to_plan(self, plan_id: int, new_tasks: List[Task]) -> bool:
        session = self._get_session()
        try:
            max_index = session.query(func.max(TaskModel.order_index)).filter(
                TaskModel.plan_id == plan_id
            ).scalar() or -1
            
            for i, task in enumerate(new_tasks):
                task_model = TaskModel(
                    plan_id=plan_id,
                    title=task.title,
                    description=task.description,
                    status=task.status.value,
                    priority=task.priority.value,
                    order_index=max_index + 1 + i,
                    dependencies=json.dumps(task.dependencies)
                )
                session.add(task_model)
            
            self._update_plan_progress(session, plan_id)
            session.commit()
            return True
        finally:
            session.close()
    
    def update_plan_info(self, plan_id: int, title: Optional[str] = None, 
                        description: Optional[str] = None) -> bool:
        session = self._get_session()
        try:
            plan = session.query(PlanModel).filter(PlanModel.id == plan_id).first()
            if not plan:
                return False
            
            if title:
                plan.title = title
            if description is not None:
                plan.description = description
            
            plan.updated_at = datetime.now()
            session.commit()
            return True
        finally:
            session.close()
    
    def delete_plan(self, plan_id: int) -> bool:
        session = self._get_session()
        try:
            plan = session.query(PlanModel).filter(PlanModel.id == plan_id).first()
            if not plan:
                return False
            
            session.delete(plan)
            session.commit()
            return True
        finally:
            session.close()

