# Planer MCP Server

An intelligent planning and task management MCP server built with FastMCP that provides sophisticated planning tools optimized for software engineering projects.

## Features

- **🤖 LLM-Powered Task Generation**: Uses LLM sampling to generate context-aware, high-quality task breakdowns
- **💬 Interactive Elicitation**: Asks clarifying questions to ensure requirements are well-understood
- **✅ Plan Validation**: Preview and confirm plans before saving, with regeneration option
- **📊 Progress Reporting**: Real-time progress updates during plan creation
- **🎯 Engineering-Focused**: Optimized prompts for coding, debugging, system design, and feature development
- **⏱️ Automatic Time Tracking**: Track actual time via plan/task creation and completion timestamps
- **📄 Pagination**: Efficient handling of large plan lists (30 plans per page)
- **🔍 Smart Filtering**: Hide completed plans by default, focus on active work
- **💾 Persistent Storage**: SQLite database for reliable data persistence
- **🏷️ Category-based Planning**: Different planning strategies based on task categories

## How It Works

When you create a new plan, the server uses an intelligent, LLM-driven workflow:

1. **🧠 LLM Analyzes Requirements** (10% progress)
   - The LLM evaluates if there's enough information
   - Determines what's missing (if anything)
   - Only asks for clarification when truly needed
   - Users are NOT bothered unnecessarily!

2. **💬 Smart Elicitation** (Conditional)
   - **IF** LLM needs more info → Asks specific, targeted questions
   - **ELSE** → Proceeds directly to task generation
   - Example: "Build REST API" might not need questions
   - Example: "Migrate system" likely needs clarification on tech stack

3. **🤖 Generates Tasks with LLM** (30-60% progress)
   - Uses LLM sampling to create context-aware tasks
   - Applies category-specific planning strategies
   - Considers dependencies and priorities
   - Generates detailed task descriptions

4. **👀 Shows Preview & Confirms** (80% progress)
   - Displays the proposed plan
   - You can: accept, request modifications, or cancel

5. **🔁 Regenerates if Needed**
   - If you request changes, LLM regenerates with your feedback
   - Iterative refinement until you're satisfied

6. **💾 Saves to Database** (95-100% progress)
   - Stores the validated, high-quality plan

## Tools Available

### `new_plan` ⭐ Enhanced with Intelligent LLM-Driven Workflow

Creates a new plan with intelligent task breakdown. The LLM decides when to ask for clarification - users are only bothered when necessary!

**Smart Workflow:**
1. **LLM analyzes** your request (10% progress)
2. **Conditionally elicits** only if LLM needs more info
3. **Generates tasks** using LLM sampling (30-60% progress)
4. **Shows preview** and asks for confirmation (80% progress)
5. **Regenerates** if you request modifications
6. **Saves** validated plan (95-100% progress)

**Parameters:**
- `title`: Plan title (max 200 chars)
- `goal`: Main goal or objective (max 500 chars)
- `category`: One of: project, personal, learning, business, creative, research, maintenance
- `description` (optional): Detailed description
- `additional_context` (optional): Additional context for better planning

**Key Features:**
- 🧠 **Smart Elicitation**: LLM decides when questions are needed
- 🎯 **No Unnecessary Interruptions**: Only asks when truly required
- 📊 **Progress Reporting**: Real-time updates (10%, 30%, 60%, 80%, 95%, 100%)
- 📝 **Comprehensive Logging**: Info, warning, error, debug messages
- 🤖 **LLM-Powered**: High-quality, context-aware task generation
- 🔁 **Feedback Loop**: Request modifications and regenerate
- 🛡️ **Reliable**: Falls back to templates if LLM fails

### `list_plans`

List plans with pagination and filtering.

**Parameters:**
- `include_completed` (optional, default: False): Include completed plans
- `page` (optional, default: 1): Page number (30 plans per page)

### `get_plan`

Retrieve detailed information about a specific plan.

**Parameters:**
- `plan_id`: ID of the plan to retrieve

### `update_task_status`

Update the status of specific tasks within a plan.

**Parameters:**
- `plan_id`: ID of the plan containing the tasks
- `task_ids`: List of task IDs to update
- `status`: One of: pending, in_progress, completed, deleted
- `notes` (optional): Notes about the status change

### `update_plan`

Update existing plan by adding new tasks or changing plan info.

**Parameters:**
- `plan_id`: ID of the plan to update
- `title` (optional): New title
- `description` (optional): New description
- `new_tasks` (optional): List of new task titles to add
- `additional_context` (optional): Additional context for the update

### `delete_plan`

Permanently delete a plan and all its tasks from the database.

**Parameters:**
- `plan_id`: ID of the plan to delete

## Installation

```bash
cd planer-mcp

uv venv

uv pip install -e ".[dev]"
```

## Usage

### Run with Python Module

```bash
# Recommended for MCP clients
uv run python -m src.planer_mcp.server
```

### Run with main.py

```bash
python main.py
# or
uv run python main.py
```

### Configure in Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "planer": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Projects/mcp/planer-mcp",
        "run",
        "python",
        "-m",
        "src.planer_mcp.server"
      ]
    }
  }
}
```

Change the `--directory` path to match your project location.

## Development

```bash
make test         # Run tests
make format       # Format code
make lint         # Lint code
make type-check   # Type checking
```

## Architecture

- `src/planer_mcp/server.py` - FastMCP server implementation
- `src/planer_mcp/models/schemas.py` - Pydantic data models
- `src/planer_mcp/database/models.py` - SQLAlchemy ORM models
- `src/planer_mcp/database/manager.py` - Database operations with query builder
- `src/planer_mcp/planning/engine.py` - Planning logic
- `src/planer_mcp/planning/formatter.py` - Output formatting
- `src/planer_mcp/prompts/templates.py` - Category-specific prompts

## Categories

### Project (Software Engineering)
- Requirements analysis and specification
- System architecture and design
- Database schema and data modeling
- API design and implementation
- Frontend/backend development
- Testing strategy and implementation
- CI/CD setup and deployment
- Code review and quality gates
- Performance optimization
- Documentation and security

### Learning (Skill Development)
- Progressive skill building
- Hands-on coding exercises
- Real project development
- Code review practice
- Testing and debugging
- Performance optimization
- Architecture patterns

### Business (Product Development)
- Market research and validation
- MVP feature definition
- Technical architecture
- Monitoring and analytics
- User feedback integration
- Iterative development

### Creative (Design)
- User research and personas
- Design system and components
- Wireframing and prototyping
- Accessibility considerations
- Design-dev handoff

### Research (Investigation)
- Problem statement definition
- Technology evaluation
- Proof of concept development
- Performance benchmarking
- Documentation of findings

### Maintenance (Refactoring)
- Code audit and technical debt
- Dependency updates and patches
- Test coverage improvement
- Documentation updates
- Performance profiling

## Example Usage

### Creating a Plan (LLM-Driven, Smart Elicitation)

**Example 1: Sufficient Information (No Elicitation)**
```
User: Create plan for "Build REST API with FastAPI"

Server: [Progress 10%] Analyzing requirements...
Server: [Info] Sufficient information provided, generating task list...
Server: [Progress 30%] Generating tasks with LLM...
Server: [Progress 60%] Parsing generated tasks...
Server: [Info] Generated 12 tasks from LLM
Server: [Progress 80%] Validating plan...

[Plan Preview shows 12 detailed tasks]

Server: Does this plan look correct?
- Type 'yes' to save
- Type modifications to regenerate
- Type 'cancel' to abort

User: yes

Server: [Progress 100%] Plan created successfully!
```

**Example 2: LLM Needs Clarification (Smart Elicitation)**
```
User: Create plan for "Migrate legacy system to cloud"

Server: [Progress 10%] Analyzing requirements...
Server: [Info] LLM needs clarification: Critical tech stack info missing

To create an effective plan for 'Migrate legacy system to cloud', please provide:
1. What is the current technology stack?
2. Which cloud provider (AWS/Azure/GCP)?
3. What's the current deployment architecture?
4. What's the timeline/phased approach preference?

User: Currently on-premise Java monolith with MySQL. Moving to AWS. 
      3-month timeline, want microservices architecture.

Server: [Info] Additional context received, generating optimized task list...
Server: [Progress 30%] Generating tasks with LLM...
Server: [Info] Generated 18 tasks from LLM
...
```

**Example 3: Request Modifications**
```
[After plan preview]

User: Add more testing tasks and include performance benchmarks

Server: [Info] Regenerating plan with user feedback...
Server: [Info] Regenerated plan with 16 tasks
Server: [Progress 95%] Saving plan to database...
```

### Listing Active Plans

```bash
# Only active (incomplete) plans
list_plans()

# Include completed plans
list_plans(include_completed=True)

# Pagination
list_plans(page=2)
```

### Managing Tasks

```bash
# Mark tasks complete
update_task_status(plan_id=1, task_ids=[1, 2, 3], status="completed")

# Set tasks in progress
update_task_status(plan_id=1, task_ids=[4, 5], status="in_progress", notes="Started backend work")
```

## Best Practices

- All `__init__.py` files ONLY contain imports/exports
- Code is in properly named files (schemas.py, manager.py, etc.)
- SQLAlchemy query builder for all database operations
- Type hints throughout
- FastMCP for clean, modern MCP server implementation

## Testing

```bash
uv run pytest tests/ -v
```

All 12 tests passing with 100% coverage of core functionality.
