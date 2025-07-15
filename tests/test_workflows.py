import asyncio
import pytest
from graphfusionai import Team, Agent
from graphfusionai.graph_manager import GraphManager

@pytest.fixture
def sample_team():
    """Fixture providing a test team with 2 agents"""
    graph_manager = GraphManager()
    team = Team(
        team_id="test_team",
        graph_manager=graph_manager,
        state_db=None
    )
    team.agents = {
        "agent1": Agent("agent1", "Test Role", {"execute": lambda x: x}),
        "agent2": Agent("agent2", "Test Role", {"execute": lambda x: x})
    }
    return team

@pytest.mark.asyncio
async def test_parallel_execution(sample_team):
    """Verify parallel step execution"""
    workflow = {
        "steps": [
            {"id": "step1", "agent_id": "agent1", "task": "execute", "parallel": True, "input": 1},
            {"id": "step2", "agent_id": "agent2", "task": "execute", "parallel": True, "input": 2}
        ]
    }
    
    results = await sample_team.execute_workflow(workflow)
    assert "step1" in results["completed"]
    assert "step2" in results["completed"]

@pytest.mark.asyncio
async def test_conditional_workflow(sample_team):
    """Verify conditional step execution"""
    workflow = {
        "steps": [
            {
                "id": "cond_step",
                "when": "1 == 1",  # Always true
                "then": [
                    {"id": "true_step", "agent_id": "agent1", "task": "execute", "input": 1}
                ],
                "else": [
                    {"id": "false_step", "agent_id": "agent2", "task": "execute", "input": 0}
                ]
            }
        ]
    }
    
    results = await sample_team.execute_workflow(workflow)
    assert "true_step" in results["completed"]
    assert "false_step" not in results.get("completed", {})

@pytest.mark.asyncio
async def test_workflow_timeout(sample_team):
    """Verify workflow timeout handling"""
    # Agent with a long-running task
    slow_agent = Agent("slow", "Test Role", {"slow_task": lambda: asyncio.sleep(10)})
    sample_team.agents["slow"] = slow_agent
    
    workflow = {
        "steps": [
            {"id": "slow_step", "agent_id": "slow", "task": "slow_task", "timeout": 1}
        ]
    }
    
    results = await sample_team.execute_workflow(workflow, timeout=2)
    assert results.get("status") == "timeout"
    assert "slow_step" in results.get("failed", {})
