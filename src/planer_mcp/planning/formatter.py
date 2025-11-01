from typing import List

from ..models.schemas import Plan, Task, TaskStatus, Priority

class PlanFormatter:
    @staticmethod
    def format_plan_summary(plan: Plan) -> str:
        status_emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.DELETED: "🗑️"
        }
        
        header = f"{status_emoji.get(plan.status, '📋')} {plan.title}\n"
        header += f"Category: {plan.category.value.upper()}\n"
        header += f"Goal: {plan.goal}\n"
        header += f"Progress: {plan.completed_tasks}/{plan.total_tasks} tasks ({plan.progress_percentage:.1f}%)\n"
        
        return header
    
    @staticmethod
    def format_plan_detailed(plan: Plan) -> str:
        result = PlanFormatter.format_plan_summary(plan)
        
        if plan.description:
            result += f"\nDescription: {plan.description}\n"
        
        if plan.tasks:
            result += "\n📝 Tasks:\n"
            for i, task in enumerate(plan.tasks, 1):
                status_icon = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.DELETED: "🗑️"
                }.get(task.status, "•")
                
                priority_icon = {
                    Priority.LOW: "🟢",
                    Priority.MEDIUM: "🟡",
                    Priority.HIGH: "🟠",
                    Priority.CRITICAL: "🔴"
                }.get(task.priority, "")
                
                result += f"\n{i}. {status_icon} {priority_icon} {task.title}"
                if task.description:
                    result += f"\n   {task.description}"
                if task.dependencies:
                    deps = ", ".join(str(d+1) for d in task.dependencies)
                    result += f"\n   Dependencies: {deps}"
        
        return result
    
    @staticmethod
    def format_plans_list(plans: List[Plan]) -> str:
        if not plans:
            return "No plans found."
        
        result = f"Found {len(plans)} plan(s):\n\n"
        for plan in plans:
            result += f"ID {plan.id}: {plan.title}\n"
            result += f"  Category: {plan.category.value} | Progress: {plan.progress_percentage:.0f}%\n"
            result += f"  Status: {plan.status.value} | Tasks: {plan.completed_tasks}/{plan.total_tasks}\n\n"
        
        return result

