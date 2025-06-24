import threading
import asyncio
from typing import Dict, List, Callable, Any, Optional
import logging
from .persistence import AgentStateDB, AgentState
import time

logger = logging.getLogger(__name__)

class Agent:
    """
    Represents an individual AI agent in a multi-agent team.
    Handles task execution, communication, and knowledge sharing.
    
    Attributes:
        agent_id: Unique identifier for the agent
        role: Functional role within the team
        capabilities: Dictionary of functions the agent can perform
        team: Reference to the Team this agent belongs to
        graph_manager: Reference to the knowledge graph manager
        memory: Local memory store for the agent
    """
    
    def __init__(self, agent_id: str, role: str, capabilities: Dict[str, Callable], 
                 graph_manager, team=None, state_db: AgentStateDB = None):
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities
        self.team = team
        self.graph_manager = graph_manager
        self.memory = {}
        self.task_queue = []
        self.status = "idle"  # idle, busy, error
        self.state_db = state_db
        
        # Load existing state if available
        if state_db:
            self.load_state()
        
        # Register agent in knowledge graph
        self.graph_manager.add_agent(self.agent_id, {"role": self.role})

    async def assign_to_team(self, team):
        """Assign this agent to a team"""
        self.team = team
        self.graph_manager.add_connection(self.agent_id, team.team_id, 
                                         relation="member_of")

    async def add_capability(self, name: str, function: Callable):
        """Add a new capability to the agent"""
        self.capabilities[name] = function

    async def execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute a task asynchronously"""
        if not self.capabilities:
            raise RuntimeError("No capabilities defined for agent")
        
        logger.debug(f"Agent {self.agent_id} executing task: {task}")
        logger.debug(f"Agent team: {self.team}")
        
        task_type = task.get("type")
        if task_type not in self.capabilities:
            raise ValueError(f"Unsupported task type: {task_type}")
        
        capability = self.capabilities[task_type]
        try:
            # If capability is async function, await it
            if asyncio.iscoroutinefunction(capability):
                result = await capability(**task.get("parameters", {}))
            else:
                # Run synchronous function in thread pool
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, capability, **task.get("parameters", {})
                )
            self.team.report_task_completion(self.agent_id, task, result)
            return result
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.team.report_task_failure(self.agent_id, task, str(e))
            raise

    async def request_help(self, task: Dict[str, Any], recipient_id: str):
        """Request help from another agent for a specific task"""
        if not isinstance(recipient_id, str):
            raise TypeError(f"recipient_id must be a string, got {type(recipient_id)}: {recipient_id}")
        if not self.team:
            raise RuntimeError("Agent not part of a team")
        await self.team.send_message(self.agent_id, recipient_id, {
            "type": "help_request",
            "task": task
        })

    async def send_message(self, recipient_id: str, content: Dict):
        """Send a message to another agent"""
        if not self.team:
            raise RuntimeError("Agent not part of a team")
        await self.team.send_message(self.agent_id, recipient_id, content)

    async def receive_message(self, sender_id: str, content: Dict):
        """Handle incoming message"""
        # Default implementation - can be overridden
        print(f"{self.agent_id} received message from {sender_id}: {content}")
        
        if content["type"] == "help_request":
            # Automatically accept help requests
            await self.execute_task(content["task"])

    async def store_memory(self, key: str, value: Any):
        """Store information in local memory"""
        self.memory[key] = value

    async def recall_memory(self, key: str):
        """Retrieve information from shared knowledge graph or local memory"""
        # First try the knowledge graph
        result = self.graph_manager.query_knowledge(key)
        if result:
            return result
        # Fallback to local memory
        return self.memory.get(key)

    async def contribute_to_knowledge_graph(self, key: str, value: Any):
        """Contribute knowledge to the shared graph"""
        self.graph_manager.add_knowledge(self.agent_id, key, value)

    def load_state(self):
        """Load agent state from database"""
        if self.state_db:
            state = self.state_db.load_state(self.agent_id)
            if state:
                self.status = state.status
                # Note: Capabilities are functions so we can't directly restore
                # We'll just store capability names for now
                # Actual capabilities must be re-registered
                self.memory = state.memory
                
    async def save_state(self):
        """Save current agent state to database"""
        if self.state_db:
            state = AgentState(
                agent_id=self.agent_id,
                status=self.status,
                capabilities=list(self.capabilities.keys()),
                memory=self.memory,
                last_updated=time.time()
            )
            self.state_db.save_state(state)

# Example usage
if __name__ == "__main__":
    from graph_manager import GraphManager
    from persistence import AgentStateDB
    
    gm = GraphManager("graph_data.json")
    state_db = AgentStateDB("agent_states.json")
    agent1 = Agent("Agent1", "planner", {}, gm, state_db=state_db)
    agent2 = Agent("Agent2", "executor", {}, gm, state_db=state_db)
    asyncio.run(agent1.assign_to_team(None))  # Assign to a team
    asyncio.run(agent2.assign_to_team(None))  # Assign to a team
    asyncio.run(agent1.send_message("Agent2", {"type": "help_request", "task": {"type": "data_processing"}}))
    asyncio.run(agent1.store_memory("task", "Optimize pipeline"))
    print(asyncio.run(agent1.recall_memory("task")))
    asyncio.run(agent1.contribute_to_knowledge_graph("strategy", "Divide and conquer"))
    asyncio.run(agent1.save_state())
