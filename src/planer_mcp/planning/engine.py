import json
from typing import Dict, List, Any

from ..models.schemas import Plan, Task, PlanRequest, PlanCategory, Priority, TaskStatus

class PlanningEngine:
    def __init__(self) -> None:
        pass
    
    def parse_llm_tasks(self, llm_response: str) -> List[Dict[str, Any]]:
        try:
            tasks = json.loads(llm_response)
            if isinstance(tasks, list):
                return tasks
        except json.JSONDecodeError:
            pass
        
        return []
    
    def create_plan_from_tasks(self, request: PlanRequest, tasks: List[Task]) -> Plan:
        plan = Plan(
            title=request.title,
            description=request.description,
            category=request.category,
            goal=request.goal,
            status=TaskStatus.PENDING,
            total_tasks=len(tasks),
            completed_tasks=0,
            tasks=tasks
        )
        
        return plan

