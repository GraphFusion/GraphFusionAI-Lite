import pytest
import pytest_asyncio
import asyncio
from graphfusionai import Team, Agent, GraphManager

@pytest.fixture
def sample_team():
    """Fixture providing a properly initialized test team with 2 agents"""
    graph_manager = GraphManager()
    team = Team(
        team_id="test_team",
        graph_manager=graph_manager,
        state_db=None
    )
    
    # Track team state
    team._is_running = False
    
    # Create and add agents with proper capability functions
    team.agents = {
        "agent1": Agent(
            agent_id="agent1",
            role="Test Role",
            capabilities={"execute": lambda x: {"result": x}},
            graph_manager=graph_manager,
            team=team
        ),
        "agent2": Agent(
            agent_id="agent2",
            role="Test Role",
            capabilities={"execute": lambda x: {"result": x}},
            graph_manager=graph_manager,
            team=team
        )
    }
    
    # Add property for state checking
    @property
    def is_running(self):
        return getattr(self, '_is_running', False)
    
    Team.is_running = is_running
    
    # Initialize team
    team._is_running = True
    yield team
    team._is_running = False

@pytest.mark.asyncio
async def test_parallel_execution(sample_team):
    """Verify parallel step execution"""
    workflow = {
        "steps": [
            {
                "id": "step1", 
                "agent_id": "agent1", 
                "task": "execute", 
                "parallel": True, 
                "input": 1,
                "timeout": 1
            },
            {
                "id": "step2", 
                "agent_id": "agent2", 
                "task": "execute", 
                "parallel": True, 
                "input": 2,
                "timeout": 1
            }
        ]
    }
    
    # Ensure team is running
    sample_team._is_running = True
    
    results = await sample_team.execute_workflow(workflow)
    assert "step1" in results.get("completed", {})
    assert "step2" in results.get("completed", {})

@pytest.mark.asyncio
async def test_parallel_execution_with_dependencies(sample_team):
    """Verify parallel step execution with dependencies"""
    workflow = {
        "steps": [
            {
                "id": "step1",
                "agent_id": "agent1", 
                "task": "execute",
                "parallel": True,
                "input": {"value": 1},
                "timeout": 1
            },
            {
                "id": "step2",
                "agent_id": "agent2",
                "task": "execute", 
                "parallel": True,
                "input": {"value": 2},
                "timeout": 1
            },
            {
                "id": "step3",
                "agent_id": "agent1",
                "task": "execute",
                "depends_on": ["step1", "step2"],
                "input": {"value": 3},
                "timeout": 1
            }
        ]
    }

    results = await sample_team.execute_workflow(workflow)
    
    # Verify all steps completed
    assert results["status"] == "completed"
    assert set(results["completed"].keys()) == {"step1", "step2", "step3"}
    assert not results["failed"]
    
    # Verify step3 executed after parallel steps
    assert results["completed"]["step1"]["timestamp"] < results["completed"]["step3"]["timestamp"]
    assert results["completed"]["step2"]["timestamp"] < results["completed"]["step3"]["timestamp"]

@pytest.mark.asyncio
async def test_mixed_workflow(sample_team):
    """Verify workflow with both parallel and serial steps"""
    workflow = {
        "steps": [
            {
                "id": "parallel1",
                "agent_id": "agent1",
                "task": "execute",
                "parallel": True,
                "input": {"value": 1},
                "timeout": 1
            },
            {
                "id": "serial1",
                "agent_id": "agent2",
                "task": "execute",
                "depends_on": ["parallel1"],
                "input": {"value": 2}, 
                "timeout": 1
            },
            {
                "id": "parallel2",
                "agent_id": "agent1",
                "task": "execute",
                "parallel": True,
                "depends_on": ["serial1"],
                "input": {"value": 3},
                "timeout": 1
            }
        ]
    }

    results = await sample_team.execute_workflow(workflow)
    
    # Verify execution order
    assert results["status"] == "completed"
    assert len(results["completed"]) == 3
    assert results["completed"]["parallel1"]["timestamp"] < results["completed"]["serial1"]["timestamp"]
    assert results["completed"]["serial1"]["timestamp"] < results["completed"]["parallel2"]["timestamp"]

@pytest.mark.asyncio
async def test_conditional_workflow(sample_team):
    """Verify conditional step execution"""
    workflow = {
        "steps": [
            {
                "id": "cond_step",
                "when": "1 == 1",  # Always true
                "then": [
                    {
                        "id": "true_step", 
                        "agent_id": "agent1", 
                        "task": "execute", 
                        "input": 1,
                        "timeout": 1
                    }
                ],
                "else": [
                    {
                        "id": "false_step", 
                        "agent_id": "agent2", 
                        "task": "execute", 
                        "input": 0,
                        "timeout": 1
                    }
                ]
            }
        ]
    }
    
    # Ensure team is running
    sample_team._is_running = True
    
    results = await sample_team.execute_workflow(workflow)
    assert "true_step" in results.get("completed", {})
    assert "false_step" not in results.get("completed", {})

@pytest.mark.asyncio
async def test_workflow_timeout(sample_team):
    """Verify workflow timeout handling"""
    # Create slow agent with proper capability
    slow_agent = Agent(
        agent_id="slow", 
        role="Test Role",
        capabilities={"slow_task": lambda: asyncio.sleep(10)},
        graph_manager=sample_team.graph_manager,
        team=sample_team
    )
    sample_team.agents["slow"] = slow_agent
    
    workflow = {
        "steps": [
            {"id": "slow_step", "agent_id": "slow", "task": "slow_task", "timeout": 1}
        ]
    }
    
    results = await sample_team.execute_workflow(workflow, timeout=2)
    assert results.get("status", "").lower() in ["timeout", "failed"]  # More flexible check
    assert "slow_step" in results.get("failed", {})

@pytest.mark.asyncio
async def test_parallel_failure(sample_team):
    """Verify workflow handles parallel step failures"""
    workflow = {
        "steps": [
            {
                "id": "step1",
                "agent_id": "agent1",
                "task": "execute",
                "parallel": True,
                "input": {"value": 1},
                "timeout": 1
            },
            {
                "id": "step2", 
                "agent_id": "agent2",
                "task": "fail",  # This will fail
                "parallel": True,
                "input": {"value": 2},
                "timeout": 1
            },
            {
                "id": "step3",
                "agent_id": "agent1",
                "task": "execute",
                "depends_on": ["step1", "step2"],
                "input": {"value": 3},
                "timeout": 1
            }
        ]
    }

    results = await sample_team.execute_workflow(workflow)
    
    # Verify partial completion
    assert results["status"] == "partial"
    assert "step1" in results["completed"]
    assert "step2" in results["failed"]
    assert "step3" not in results["completed"]  # Shouldn't run due to dependency

@pytest.mark.asyncio
async def test_parallel_timeout(sample_team):
    """Verify parallel steps respect timeouts"""
    # Add a slow agent
    slow_agent = Agent(
        agent_id="slow",
        role="Tester",
        capabilities={"slow_task": lambda: asyncio.sleep(10)},
        graph_manager=sample_team.graph_manager,
        team=sample_team
    )
    sample_team.agents["slow"] = slow_agent

    workflow = {
        "steps": [
            {
                "id": "fast_step",
                "agent_id": "agent1",
                "task": "execute",
                "parallel": True, 
                "input": {"value": 1},
                "timeout": 1
            },
            {
                "id": "slow_step",
                "agent_id": "slow",
                "task": "slow_task",
                "parallel": True,
                "timeout": 1
            }
        ]
    }

    results = await sample_team.execute_workflow(workflow, timeout=2)
    assert results["status"] in ["partial", "failed"]
    assert "fast_step" in results["completed"]
    assert "slow_step" in results["failed"]
