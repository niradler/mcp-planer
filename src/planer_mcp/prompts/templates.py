from typing import Dict

from ..models.schemas import PlanCategory

class PlanningPrompts:
    BASE_PROMPT = """
You are an expert software engineering project planner. Break down the given goal into comprehensive, actionable tasks.

GOAL: {goal}
CATEGORY: {category}
DESCRIPTION: {description}
ADDITIONAL CONTEXT: {additional_context}

Create a detailed task breakdown following these guidelines:
- Each task should be specific, measurable, and actionable
- Tasks should be ordered logically (dependencies considered)
- Set appropriate priorities (low, medium, high, critical)
- Consider potential dependencies between tasks
- Aim for 5-20 tasks depending on complexity

Respond with a JSON array of task objects, each containing:
- "title": Brief, clear task description
- "description": More detailed explanation if needed
- "priority": One of ["low", "medium", "high", "critical"]
- "dependencies": Array of task indices that must be completed first (0-based)

Focus on the specific planning approach for the {category} category.
"""

    CATEGORY_SPECIFIC = {
        PlanCategory.PROJECT: """
For SOFTWARE PROJECT planning, focus on:
- Requirements analysis and specification
- System architecture and design decisions
- Database schema and data modeling
- API design and endpoint planning
- Frontend component hierarchy
- Backend service architecture
- Authentication and authorization
- Testing strategy (unit, integration, e2e)
- Deployment and CI/CD setup
- Code review and quality gates
- Performance optimization points
- Documentation and API specs
- Security considerations
- Error handling and logging

Break down into phases: Planning, Design, Implementation, Testing, Deployment.
""",

        PlanCategory.PERSONAL: """
For PERSONAL DEVELOPMENT planning, focus on:
- Clear, achievable milestones
- Skill acquisition and practice
- Small, manageable daily tasks
- Progress tracking mechanisms
- Celebration points
- Flexibility for life circumstances
- Balance and sustainability

Make tasks achievable and personally meaningful.
""",

        PlanCategory.LEARNING: """
For LEARNING/SKILL DEVELOPMENT planning, focus on:
- Fundamentals before advanced concepts
- Hands-on coding exercises
- Building real projects
- Code review and best practices
- Reading documentation and source code
- Testing and debugging practice
- Performance and optimization
- Code organization and architecture
- Version control workflows
- Collaboration patterns

Structure learning through practical application and iteration.
""",

        PlanCategory.BUSINESS: """
For BUSINESS/PRODUCT planning, focus on:
- Market research and validation
- MVP feature definition
- User stories and acceptance criteria
- Technical architecture decisions
- Scalability considerations
- Monitoring and analytics
- Go-to-market strategy
- Performance metrics and KPIs
- Iterative development cycles
- User feedback integration

Include strategic, tactical, and operational levels.
""",

        PlanCategory.CREATIVE: """
For CREATIVE/DESIGN planning, focus on:
- User research and personas
- Design system and components
- Wireframing and prototyping
- User experience flows
- Visual design and branding
- Accessibility considerations
- Responsive design
- Design-dev handoff
- Iterative feedback cycles
- Usability testing

Balance creativity with systematic execution.
""",

        PlanCategory.RESEARCH: """
For RESEARCH/INVESTIGATION planning, focus on:
- Problem statement definition
- Literature review and prior art
- Technology evaluation
- Proof of concept development
- Performance benchmarking
- Edge case analysis
- Documentation of findings
- Presentation preparation

Follow systematic research methodology.
""",

        PlanCategory.MAINTENANCE: """
For MAINTENANCE/REFACTORING planning, focus on:
- Code audit and technical debt assessment
- Dependency updates and security patches
- Performance profiling and optimization
- Test coverage improvement
- Documentation updates
- Refactoring priorities
- Breaking change migration
- Backward compatibility
- Deployment strategy
- Rollback procedures

Emphasize safety, testing, and gradual improvement.
"""
    }

    @classmethod
    def get_planning_prompt(cls, goal: str, category: PlanCategory, 
                          description: str = "", additional_context: str = "") -> str:
        category_guidance = cls.CATEGORY_SPECIFIC.get(category, "")
        
        return cls.BASE_PROMPT.format(
            goal=goal,
            category=category.value,
            description=description or "No description provided.",
            additional_context=additional_context or "No additional context provided."
        ) + "\n" + category_guidance

    @classmethod
    def get_update_prompt(cls, plan_title: str, current_tasks: str, 
                         update_request: str, additional_context: str = "") -> str:
        return f"""
You are an expert project planner updating an existing plan.

CURRENT PLAN: {plan_title}
EXISTING TASKS: {current_tasks}
UPDATE REQUEST: {update_request}
ADDITIONAL CONTEXT: {additional_context}

Provide an updated task list that:
- Incorporates the requested changes
- Maintains logical task ordering and dependencies
- Preserves completed tasks unless explicitly requested to modify
- Adds new tasks where appropriate
- Adjusts priorities as needed

Respond with a JSON object containing:
- "tasks_to_add": Array of new task objects (same format as before)
- "tasks_to_modify": Array of objects with "task_id" and updated fields
- "tasks_to_remove": Array of task IDs to delete
- "explanation": Brief explanation of the changes made

Focus on maintaining plan coherence while implementing the requested updates.
"""
