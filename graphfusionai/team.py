import threading
from typing import Dict, List, Any, Optional
import logging
from .agent import Agent
from .graph_manager import GraphManager
from .persistence import TeamStateDB, TeamState
import time
import asyncio

logger = logging.getLogger(__name__)

class Team:
    """
    Represents a team of agents that collaborate to achieve common goals.
    
    Attributes:
        team_id: Unique identifier for the team
        agents: Dictionary of agents in the team, keyed by agent ID
        graph_manager: Reference to the shared knowledge graph
        task_queue: Queue of tasks to be assigned
        communication_graph: Graph representing communication pathways
        shared_state: Dictionary for shared state among team members
    """
    
    def __init__(
        self,
        team_id: str,
        graph_manager: GraphManager,
        state_db: Optional[TeamStateDB] = None,
        auto_save_interval: int = 60
    ):
        self.team_id = team_id
        self.graph_manager = graph_manager
        self.agents = {}  # Dictionary of agent_id to Agent
        self.task_queue = []
        self.communication_graph = {}
        self.shared_state = {}
        self.lock = threading.Lock()
        self.state_db = state_db
        self.auto_save_interval = auto_save_interval
        self._auto_save_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # Register the team in the knowledge graph
        self.graph_manager.add_agent(self.team_id, {"type": "team"})
        
        # Load existing state if available
        if state_db:
            self.load_state()
    
    async def add_agent(self, agent: Agent):
        """Add an agent to the team"""
        with self.lock:
            self.agents[agent.agent_id] = agent
            agent.team = self  # Set the agent's team reference
            # Add agent to communication graph
            self.graph_manager.add_agent(agent.agent_id, {"role": agent.role})
            # Connect agent to team
            self.graph_manager.add_connection(agent.agent_id, self.team_id, "member")
        
    def remove_agent(self, agent_id: str):
        """Remove an agent from the team"""
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                if agent_id in self.communication_graph:
                    del self.communication_graph[agent_id]
                # Remove from communication graph entries
                for connections in self.communication_graph.values():
                    if agent_id in connections:
                        connections.remove(agent_id)
    
    def add_task(self, task: Dict):
        """Add a task to the team's queue"""
        with self.lock:
            self.task_queue.append(task)
    
    async def execute_task(self, agent_id: str, task: Dict) -> Any:
        """Execute a task and return its result."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found in team")

        try:
            task_type = task.get("task", "execute")  # Default to "execute" if not specified
            result = await agent.execute_capability(task_type, task.get("input", {}))
            result["timestamp"] = time.time()  # Add timestamp to track execution order
            return result
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise
    
    def broadcast(self, sender_id: str, message: Dict):
        """Broadcast a message to all agents in the team."""
        for agent_id in self.agents:
            if agent_id != sender_id:
                asyncio.create_task(self.send_message(sender_id, agent_id, message))
    
    async def send_message(self, sender_id: str, recipient_id: str, content: Dict):
        """Send a message from one agent to another"""
        logger.debug(f"Sending message from {sender_id} to {recipient_id}")
        logger.debug(f"Agents in team: {list(self.agents.keys())}")
        if recipient_id not in self.agents:
            raise ValueError(f"Recipient agent {recipient_id} not found in team")
            
        # Record communication
        self.graph_manager.add_communication(sender_id, recipient_id, content)
        
        # Deliver message
        await self.agents[recipient_id].receive_message(sender_id, content)
    
    def report_task_completion(self, agent_id: str, task: Dict, result: Any):
        """Handle task completion report"""
        # Update shared state or knowledge graph
        self.graph_manager.add_knowledge(agent_id, task["type"], result, knowledge_type=task["type"])
        
    def report_task_failure(self, agent_id: str, task: Dict, error: str):
        """Handle task failure report."""
        logger.error(f"Task {task} failed: {error}")
        self.add_task(task)  # Requeue for retry
    
    def get_agent_by_role(self, role: str) -> Optional[Agent]:
        """Find an agent by role"""
        for agent in self.agents.values():
            if agent.role == role:
                return agent
        return None
    
    def visualize_communication_graph(self):
        """Visualize the team's communication structure"""
        # This would typically use matplotlib or similar
        print(f"Communication Graph for Team {self.team_id}:")
        for sender, recipients in self.communication_graph.items():
            print(f"{sender} -> {', '.join(recipients)}")
    
    def load_state(self):
        """Load team state from database"""
        if self.state_db:
            state = self.state_db.load_state(self.team_id)
            if state:
                # Note: Agents must be re-added to the team
                # We only restore the agent IDs and task queue
                self.task_queue = state.task_queue
                # Agents will be added later via add_agent
    
    async def save_state(self):
        """Save current team state to database"""
        if self.state_db:
            state = TeamState(
                team_id=self.team_id,
                agent_ids=list(self.agents.keys()),
                task_queue=self.task_queue,
                last_updated=time.time()
            )
            self.state_db.save_state(state)

    # -------------------------------------------------------------------------
    # Workflow Execution
    # -------------------------------------------------------------------------
    async def execute_workflow(self, workflow: Dict, timeout: Optional[int] = None) -> Dict:
        """Execute a workflow with support for conditionals and parallel steps."""
        try:
            results = await asyncio.wait_for(
                self._execute_workflow_internal(workflow),
                timeout=timeout
            )
            if not results["failed"]:
                results["status"] = "completed"
            elif results["completed"]:
                results["status"] = "partial"
            else:
                results["status"] = "failed"
            return results
        except asyncio.TimeoutError:
            logger.error(f"Workflow timed out after {timeout} seconds")
            return {
                "status": "timeout",
                "completed": {},
                "failed": {}
            }

    async def _execute_workflow_internal(self, workflow: Dict) -> Dict:
        """Internal method to handle workflow execution."""
        pending = {step["id"]: step for step in workflow["steps"]}
        completed = {}
        failed = {}
        context = {}

        while pending:
            # Handle conditionals
            for step in [s for s in list(pending.values()) if "when" in s]:
                if all(dep in completed for dep in step.get("depends_on", [])):
                    condition_met = await self._evaluate_condition(step["when"], context)
                    branch_steps = step["then"] if condition_met else step.get("else", [])
                    del pending[step["id"]]
                    for new_step in branch_steps:
                        pending[new_step["id"]] = new_step

            # Find executable steps
            executable = [
                s for s in list(pending.values())
                if all(dep in completed for dep in s.get("depends_on", []))
                and "when" not in s
            ]

            if not executable:
                if not any(s.get("depends_on") for s in pending.values()):
                    logger.error("Workflow deadlock - no executable steps")
                    break
                await asyncio.sleep(0.1)
                continue

            # Handle parallel and serial execution
            parallel_steps = [s for s in executable if s.get("parallel", False)]
            serial_steps = [s for s in executable if not s.get("parallel", False)]

            if parallel_steps:
                tasks = []
                for step in parallel_steps:
                    task = asyncio.create_task(
                        self._execute_step(step, completed, failed)
                    )
                    tasks.append(task)
                    del pending[step["id"]]
                await asyncio.gather(*tasks)

            for step in serial_steps:
                await self._execute_step(step, completed, failed)
                del pending[step["id"]]

        return {
            "completed": completed,
            "failed": failed
        }

    async def _execute_step(self, step: Dict, completed: Dict, failed: Dict):
        """Execute a single workflow step."""
        step_id = step["id"]
        try:
            result = await self.execute_task(
                step["agent_id"],
                step
            )
            completed[step_id] = result
        except Exception as e:
            logger.error(f"Step {step_id} failed: {e}")
            failed[step_id] = {"error": str(e)}

    async def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """Evaluate a workflow condition."""
        try:
            return bool(eval(condition, {}, context))
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
