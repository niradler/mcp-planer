import pytest
from datetime import datetime

from src.planer_mcp import DatabaseManager, Plan, Task, PlanCategory, TaskStatus, Priority

@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_plans.db"
    return DatabaseManager(str(db_path))

@pytest.fixture
def sample_plan():
    return Plan(
        title="Test Project",
        description="A test project plan",
        category=PlanCategory.PROJECT,
        goal="Complete the test successfully",
        status=TaskStatus.PENDING,
        tasks=[
            Task(
                plan_id=0,
                title="Task 1",
                description="First task",
                priority=Priority.HIGH,
                order_index=0
            ),
            Task(
                plan_id=0,
                title="Task 2",
                description="Second task",
                priority=Priority.MEDIUM,
                order_index=1,
                dependencies=[0]
            )
        ]
    )

def test_database_initialization(db_manager):
    assert db_manager.db_path.exists()

def test_create_plan(db_manager, sample_plan):
    created_plan = db_manager.create_plan(sample_plan)
    
    assert created_plan.id is not None
    assert created_plan.id > 0
    assert created_plan.title == sample_plan.title
    assert created_plan.total_tasks == 2

def test_get_plan(db_manager, sample_plan):
    created_plan = db_manager.create_plan(sample_plan)
    retrieved_plan = db_manager.get_plan(created_plan.id)
    
    assert retrieved_plan is not None
    assert retrieved_plan.id == created_plan.id
    assert retrieved_plan.title == sample_plan.title
    assert len(retrieved_plan.tasks) == 2

def test_get_all_plans(db_manager, sample_plan):
    db_manager.create_plan(sample_plan)
    
    sample_plan2 = Plan(
        title="Second Plan",
        category=PlanCategory.PERSONAL,
        goal="Another goal",
        tasks=[]
    )
    db_manager.create_plan(sample_plan2)
    
    all_plans = db_manager.get_all_plans()
    assert len(all_plans) == 2

def test_get_all_plans_pagination(db_manager, sample_plan):
    for i in range(35):
        plan = Plan(
            title=f"Plan {i}",
            category=PlanCategory.PROJECT,
            goal=f"Goal {i}",
            tasks=[]
        )
        db_manager.create_plan(plan)
    
    page1 = db_manager.get_all_plans(page=1, page_size=30)
    assert len(page1) == 30
    
    page2 = db_manager.get_all_plans(page=2, page_size=30)
    assert len(page2) == 5

def test_update_task_status(db_manager, sample_plan):
    created_plan = db_manager.create_plan(sample_plan)
    task_id = created_plan.tasks[0].id
    
    success = db_manager.update_task_status([task_id], TaskStatus.COMPLETED)
    assert success is True
    
    updated_plan = db_manager.get_plan(created_plan.id)
    assert updated_plan.completed_tasks == 1
    assert updated_plan.tasks[0].status == TaskStatus.COMPLETED

def test_completed_plan_filtering(db_manager):
    completed_plan = Plan(
        title="Completed Plan",
        category=PlanCategory.PROJECT,
        goal="Completed goal",
        tasks=[
            Task(plan_id=0, title="Task 1", status=TaskStatus.COMPLETED, order_index=0)
        ]
    )
    created = db_manager.create_plan(completed_plan)
    db_manager.update_task_status([created.tasks[0].id], TaskStatus.COMPLETED)
    
    active_plans = db_manager.get_all_plans(include_completed=False)
    assert len(active_plans) == 0
    
    all_plans = db_manager.get_all_plans(include_completed=True)
    assert len(all_plans) == 1

def test_add_tasks_to_plan(db_manager, sample_plan):
    created_plan = db_manager.create_plan(sample_plan)
    
    new_tasks = [
        Task(
            plan_id=created_plan.id,
            title="New Task",
            priority=Priority.LOW,
            order_index=2
        )
    ]
    
    success = db_manager.add_tasks_to_plan(created_plan.id, new_tasks)
    assert success is True
    
    updated_plan = db_manager.get_plan(created_plan.id)
    assert updated_plan.total_tasks == 3

def test_update_plan_info(db_manager, sample_plan):
    created_plan = db_manager.create_plan(sample_plan)
    
    success = db_manager.update_plan_info(
        created_plan.id,
        title="Updated Title",
        description="Updated description"
    )
    assert success is True
    
    updated_plan = db_manager.get_plan(created_plan.id)
    assert updated_plan.title == "Updated Title"
    assert updated_plan.description == "Updated description"

def test_delete_plan(db_manager, sample_plan):
    created_plan = db_manager.create_plan(sample_plan)
    
    success = db_manager.delete_plan(created_plan.id)
    assert success is True
    
    deleted_plan = db_manager.get_plan(created_plan.id)
    assert deleted_plan is None

def test_plan_progress_percentage(sample_plan):
    sample_plan.total_tasks = 10
    sample_plan.completed_tasks = 5
    
    assert sample_plan.progress_percentage == 50.0
    
    sample_plan.total_tasks = 0
    assert sample_plan.progress_percentage == 0.0

def test_plan_is_completed():
    plan = Plan(
        title="Test",
        category=PlanCategory.PROJECT,
        goal="Test",
        total_tasks=2,
        completed_tasks=2
    )
    assert plan.is_completed is True
    
    plan.completed_tasks = 1
    assert plan.is_completed is False
