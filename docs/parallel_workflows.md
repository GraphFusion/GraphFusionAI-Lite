# Parallel Workflow Execution

## Overview
GraphFusionAI-Lite now supports parallel execution of independent workflow steps. This feature can significantly improve performance for workflows with independent tasks.

## Key Concepts
1. **Parallel Flag**: Add `"parallel": true` to workflow steps that can run concurrently
2. **Dependencies**: Parallel steps still respect dependency chains
3. **Execution Order**: Parallel steps execute before serial steps in each cycle
4. **Error Handling**: Failed parallel steps trigger retries (if configured)

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
- Use for independent, CPU-intensive tasks
- Limit concurrent steps based on available agents
- Monitor system resources during parallel execution
- Add timeout handling for critical paths

## Limitations
- Steps must be truly independent (no shared state)
- Debugging can be more complex
- Requires careful error handling
