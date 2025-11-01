from __future__ import annotations

import json
from enum import Enum
from typing import Any

from fastmcp import FastMCP, Context

from src.planer_mcp.database import DatabaseManager
from src.planer_mcp.models import Plan, PlanRequest, TaskStatus, Priority, Task, PlanCategory
from src.planer_mcp.planning import PlanningEngine, PlanFormatter
from src.planer_mcp.prompts import PlanningPrompts

mcp = FastMCP("Planer")


def _get_db() -> DatabaseManager:
    if not hasattr(_get_db, '_instance'):
        _get_db._instance = DatabaseManager("plans.db")
    return _get_db._instance


def _extract_json_from_text(text: str, expected_type: str = "array") -> Any | None:
    text = text.strip()
    
    start_char = '[' if expected_type == "array" else '{'
    end_char = ']' if expected_type == "array" else '}'
    
    if text.startswith(start_char):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    
    start_idx = text.find(start_char)
    end_idx = text.rfind(end_char)
    
    if start_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(text[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass
    
    return None


def _create_task_from_dict(task_dict: dict[str, Any], order_index: int, plan_id: int = 0) -> Task:
    priority_str = task_dict.get("priority", "medium")
    try:
        priority = Priority(priority_str)
    except ValueError:
        priority = Priority.MEDIUM
    
    return Task(
        plan_id=plan_id,
        title=task_dict.get("title", f"Task {order_index + 1}"),
        description=task_dict.get("description"),
        priority=priority,
        order_index=order_index,
        dependencies=task_dict.get("dependencies", [])
    )


@mcp.tool()
async def new_plan(
    title: str,
    goal: str,
    category: str,
    description: str | None = None,
    additional_context: str | None = None,
    ctx: Context = None
) -> str:
    """Create a new plan with intelligent task breakdown using LLM assistance.
    
    The LLM analyzes the request and only asks for clarification when needed to
    create an effective plan. Users are not bothered unnecessarily.
    
    Args:
        title: Plan title (max 200 chars)
        goal: Main goal or objective (max 500 chars)
        category: Plan category (project, personal, learning, business, creative, research, maintenance,
                  code, debugging, backend, frontend, system_design, feature_development)
        description: Optional detailed description
        additional_context: Optional additional context for better planning
        ctx: FastMCP context for elicitation and sampling (REQUIRED)
    """
    if ctx is None:
        return "Error: This tool requires MCP context to generate intelligent task breakdowns. Please use from an MCP client."
    
    try:
        plan_category = PlanCategory(category)
    except ValueError:
        return f"Invalid category: {category}. Valid categories: {', '.join(c.value for c in PlanCategory)}"
    
    db = _get_db()
    engine = PlanningEngine()
    
    await ctx.info(f"Creating plan: {title}")
    await ctx.info("Analyzing requirements...")
    
    analysis_prompt = f"""You are an expert project planner analyzing a planning request.

Title: {title}
Goal: {goal}
Category: {category}
Description: {description or "Not provided"}
Additional Context: {additional_context or "Not provided"}

Analyze this request and determine:
1. Is there enough information to create a detailed, effective task breakdown?
2. What critical information is missing (if any)?

Respond in JSON format:
{{
    "has_sufficient_info": true/false,
    "missing_info": ["list", "of", "missing", "items"] or [],
    "specific_questions": ["Question 1?", "Question 2?"] or [],
    "reasoning": "brief explanation"
}}

Only request clarification if it's truly needed for creating an effective plan."""
    
    enhanced_context = additional_context or ""
    
    try:
        analysis_result = await ctx.sample(
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        analysis_text = analysis_result.content.text if hasattr(analysis_result.content, 'text') else str(analysis_result.content)
        await ctx.debug(f"Analysis response: {analysis_text[:200]}...")
        
        analysis_data = _extract_json_from_text(analysis_text, "object")
        if not analysis_data:
            analysis_data = {"has_sufficient_info": True, "missing_info": [], "specific_questions": []}
        
        if not analysis_data.get("has_sufficient_info", True) and analysis_data.get("specific_questions"):
            await ctx.info(f"LLM needs clarification: {analysis_data.get('reasoning', 'Missing critical information')}")
            
            questions = "\n".join(f"{i+1}. {q}" for i, q in enumerate(analysis_data["specific_questions"]))
            
            clarification_result = await ctx.elicit(
                f"""To create an effective plan for '{title}', please provide:

{questions}

Enter the information (or press Enter to proceed with best effort):""",
                response_type=str
            )
            
            if clarification_result.action == "accept" and clarification_result.data:
                enhanced_context += f"\n\nUser clarifications:\n{clarification_result.data}"
                await ctx.info("Additional context received, generating optimized task list...")
            else:
                await ctx.info("Proceeding with available information...")
        else:
            await ctx.info("Sufficient information provided, generating task list...")
    
    except Exception as e:
        await ctx.warning(f"Analysis phase failed: {str(e)}, proceeding with task generation")
    
    await ctx.info("Generating tasks with LLM...")
    
    planning_prompt = PlanningPrompts.get_planning_prompt(
        goal=goal,
        category=plan_category,
        description=description or "",
        additional_context=enhanced_context
    )
    
    tasks: list[Task] = []
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            sample_result = await ctx.sample(
                messages=[{"role": "user", "content": planning_prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            await ctx.info("Parsing generated tasks...")
            
            llm_response = sample_result.content.text if hasattr(sample_result.content, 'text') else str(sample_result.content)
            await ctx.debug(f"LLM Response (attempt {attempt + 1}): {llm_response[:200]}...")
            
            tasks_data = _extract_json_from_text(llm_response, "array")
            
            if tasks_data and isinstance(tasks_data, list) and len(tasks_data) > 0:
                await ctx.info(f"✓ Generated {len(tasks_data)} tasks from LLM")
                tasks = [_create_task_from_dict(task_dict, i) for i, task_dict in enumerate(tasks_data)]
                break
            else:
                await ctx.warning(f"Attempt {attempt + 1}/{max_retries}: LLM response invalid, retrying...")
                
                if attempt < max_retries - 1:
                    planning_prompt += "\n\nIMPORTANT: You MUST respond with ONLY a valid JSON array of task objects. No explanations, no markdown, just the JSON array."
                else:
                    raise ValueError("LLM failed to generate valid task list after multiple attempts")
        
        except Exception as e:
            if attempt < max_retries - 1:
                await ctx.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}, retrying...")
            else:
                await ctx.error(f"Failed after {max_retries} attempts: {str(e)}")
                return f"❌ Failed to generate plan: LLM could not produce valid task breakdown after {max_retries} attempts.\n\nError: {str(e)}\n\nPlease try again with more specific details or contact support if the issue persists."
    
    if not tasks:
        return "❌ Failed to generate plan: No valid tasks generated. Please try again with a clearer goal description."
    
    await ctx.info("Validating plan...")
    
    plan = Plan(
        title=title,
        description=description,
        category=plan_category,
        goal=goal,
        status=TaskStatus.PENDING,
        total_tasks=len(tasks),
        completed_tasks=0,
        tasks=tasks
    )
    
    preview = PlanFormatter.format_plan_detailed(plan)
    
    confirmation_result = await ctx.elicit(
        f"""Plan Preview:

{preview}

Does this plan look correct? You can:
- Type 'yes' to save this plan
- Type modifications needed to regenerate
- Type 'cancel' to abort

Your response:""",
        response_type=str
    )
    
    if confirmation_result.action == "cancel":
        await ctx.info("Plan creation cancelled by user")
        return "Plan creation cancelled."
    
    if confirmation_result.action == "accept":
        user_response = confirmation_result.data.lower() if confirmation_result.data else ""
        
        if "cancel" in user_response or "abort" in user_response or "no" == user_response:
            await ctx.info("Plan creation cancelled by user")
            return "Plan creation cancelled."
        
        if "yes" not in user_response and len(user_response) > 10:
            await ctx.info("Regenerating plan with user feedback...")
            
            regeneration_messages = [
                {
                    "role": "user",
                    "content": f"""{planning_prompt}

Current tasks:
{json.dumps([{"title": t.title, "priority": t.priority.value, "description": t.description} for t in tasks], indent=2)}

User feedback for improvements:
{user_response}

Please regenerate the task list incorporating this feedback."""
                }
            ]
            
            try:
                regen_result = await ctx.sample(
                    messages=regeneration_messages,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                regen_response = regen_result.content.text if hasattr(regen_result.content, 'text') else str(regen_result.content)
                new_tasks_data = _extract_json_from_text(regen_response, "array")
                
                if new_tasks_data and isinstance(new_tasks_data, list):
                    tasks = [_create_task_from_dict(task_dict, i) for i, task_dict in enumerate(new_tasks_data)]
                    plan.tasks = tasks
                    plan.total_tasks = len(tasks)
                    await ctx.info(f"Regenerated plan with {len(tasks)} tasks")
            
            except Exception as e:
                await ctx.warning(f"Regeneration failed: {str(e)}, using original tasks")
    
    await ctx.info("Saving plan to database...")
    
    created_plan = db.create_plan(plan)
    
    await ctx.info("Plan created successfully!")
    
    formatted = PlanFormatter.format_plan_detailed(created_plan)
    return f"Plan created successfully! (ID: {created_plan.id})\n\n{formatted}"


@mcp.tool()
def list_plans(
    include_completed: bool = False,
    page: int = 1
) -> str:
    """List all plans with basic information.
    
    Args:
        include_completed: Include completed plans (default: False, shows only active plans)
        page: Page number for pagination (30 plans per page, default: 1)
    """
    db = _get_db()
    plans = db.get_all_plans(include_completed=include_completed, page=page, page_size=30)
    
    if not plans:
        return "No plans found." if not include_completed else "No plans found (try include_completed=False for active plans)."
    
    formatted = PlanFormatter.format_plans_list(plans)
    footer = f"\nPage {page} | Showing {len(plans)} plans | Use page={page+1} for more"
    
    return formatted + footer


@mcp.tool()
def get_plan(plan_id: int) -> str:
    """Retrieve detailed information about a specific plan.
    
    Args:
        plan_id: ID of the plan to retrieve
    """
    db = _get_db()
    plan = db.get_plan(plan_id)
    
    if not plan:
        return f"Plan with ID {plan_id} not found."
    
    return PlanFormatter.format_plan_detailed(plan)


@mcp.tool()
def update_task_status(
    plan_id: int,
    task_ids: list[int],
    status: str,
    notes: str | None = None
) -> str:
    """Update the status of specific tasks within a plan (pending, in_progress, completed, or deleted).
    
    Args:
        plan_id: ID of the plan containing the tasks
        task_ids: List of task IDs to update
        status: New status (pending, in_progress, completed, deleted)
        notes: Optional notes about the status change
    """
    try:
        task_status = TaskStatus(status)
    except ValueError:
        return f"Invalid status: {status}. Valid statuses: {', '.join(s.value for s in TaskStatus)}"
    
    db = _get_db()
    success = db.update_task_status(task_ids, task_status, notes)
    
    if not success:
        return "Failed to update tasks. Check task IDs."
    
    plan = db.get_plan(plan_id)
    if not plan:
        return "Tasks updated, but couldn't retrieve plan details."
    
    formatted = PlanFormatter.format_plan_detailed(plan)
    return f"Tasks updated successfully!\n\n{formatted}"


@mcp.tool()
def update_plan(
    plan_id: int,
    title: str | None = None,
    description: str | None = None,
    new_tasks: list[str] | None = None,
    additional_context: str | None = None
) -> str:
    """Update existing plan by adding new tasks, modifying existing ones, or changing plan info.
    
    Args:
        plan_id: ID of the plan to update
        title: New title (optional)
        description: New description (optional)
        new_tasks: List of new task titles to add (optional)
        additional_context: Additional context for the update (optional)
    """
    db = _get_db()
    
    if title or description:
        db.update_plan_info(plan_id, title, description)
    
    if new_tasks:
        tasks = [
            Task(
                plan_id=plan_id,
                title=task_title,
                priority=Priority.MEDIUM
            )
            for task_title in new_tasks
        ]
        db.add_tasks_to_plan(plan_id, tasks)
    
    plan = db.get_plan(plan_id)
    if not plan:
        return "Plan not found."
    
    formatted = PlanFormatter.format_plan_detailed(plan)
    return f"Plan updated successfully!\n\n{formatted}"


@mcp.tool()
def delete_plan(plan_id: int) -> str:
    """Delete a plan and all its tasks from the database.
    
    Args:
        plan_id: ID of the plan to delete
    """
    db = _get_db()
    plan = db.get_plan(plan_id)
    if not plan:
        return f"Plan {plan_id} not found."
    
    plan_title = plan.title
    success = db.delete_plan(plan_id)
    
    if success:
        return f"Plan '{plan_title}' (ID: {plan_id}) has been permanently deleted from the database."
    else:
        return f"Failed to delete plan {plan_id}."


if __name__ == "__main__":
    mcp.run()
