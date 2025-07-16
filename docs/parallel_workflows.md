# Parallel and Conditional Workflows

## Overview
GraphFusionAI-Lite now supports parallel execution of independent workflow steps and conditional branching.

## Key Features
- **Parallel Execution**: Steps marked with `"parallel": true`
- **Conditional Workflows**: `when`/`then`/`else` syntax
- **Timeout Handling**: Global and per-task timeouts

## Key Concepts
1. **Parallel Flag**: Add `"parallel": true` to workflow steps that can run concurrently
2. **Dependencies**: Parallel steps still respect dependency chains
3. **Execution Order**: Parallel steps execute before serial steps in each cycle
4. **Error Handling**: Failed parallel steps trigger retries (if configured)

## Team Initialization
```python
project_team = Team(
    team_id="project_alpha",
    graph_manager=graph_manager,
    state_db=None,
    auto_save_interval=60
)
project_team.agents = {
    "analyst1": data_analyst,
    "researcher1": research_specialist
}
```

## Example
```python
workflow = {
    "steps": [
        {
            "id": "data_load",
            "agent_id": "loader",
            "task": "load_data",
            "input": {"file": "data.csv"}
        },
        {
            "id": "process_a",
            "agent_id": "processor",
            "task": "analyze",
            "parallel": True,
            "input": {"data": "{{data_load}}"},
            "depends_on": ["data_load"]
        },
        {
            "id": "process_b",
            "agent_id": "processor",
            "task": "analyze",
            "parallel": True,
            "input": {"data": "{{data_load}}"},
            "depends_on": ["data_load"]
        }
    ]
}
```

## Best Practices
1. Initialize GraphManager first
2. Set reasonable timeouts (30-60s per task)
3. Use parallel execution for independent tasks
4. Handle workflow cancellation gracefully
5. Monitor system resources during parallel execution

## Limitations
- Steps must be truly independent (no shared state)
- Debugging can be more complex
- Requires careful error handling

## Timeout Configuration
- Global workflow timeout (default: 300s)
- Per-task timeouts (recommended: 30-60s)
- Timeout error handling
