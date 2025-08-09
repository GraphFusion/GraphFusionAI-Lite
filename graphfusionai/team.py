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
        auto_save_interval: int = 60,  # New parameter
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
    
    async def assign_task(
        self, 
        agent_id: str, 
        task: Dict, 
        priority: str = "normal",
        timeout: int = 60
    ) -> Any:
        """Assign a task to an agent with timeout handling"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found in team")
        
        try:
            return await asyncio.wait_for(
                agent.execute_task(task, priority), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self.log_error(f"Task timeout: {task.get('task_id')} for agent {agent_id}")
            raise
    
    def broadcast(self, sender_id: str, message: Dict):
        """Broadcast a message to all agents in the team"""
        for agent_id in self.agents:
            if agent_id != sender_id:  # Don't send to self
                self.send_message(sender_id, agent_id, message)
    
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
        """Handle task failure report"""
        # Log error and potentially reassign
        print(f"Task {task} failed: {error}")
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

    async def start(self) -> None:
        """Start background tasks for the team, including auto-saving if enabled."""
        if self.auto_save_interval > 0 and self._auto_save_task is None:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())
            logger.info(f"Team {self.team_id} auto-save started with interval {self.auto_save_interval} seconds.")

    async def stop(self) -> None:
        """Stop background tasks for the team."""
        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
            self._auto_save_task = None
            logger.info(f"Team {self.team_id} auto-save stopped.")

    async def _auto_save_loop(self) -> None:
        """Periodically save the team's state."""
        while True:
            try:
                await asyncio.sleep(self.auto_save_interval)
                await self.save_state()
                logger.debug(f"Auto-saved state for team {self.team_id}.")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error auto-saving team {self.team_id}: {e}", exc_info=True)

    async def execute_workflow(self, workflow: Dict, timeout: Optional[float] = 300) -> Dict:
        """
        Execute workflow with timeout protection
        Returns:
            Dict: {
                'status': 'completed'|'partial'|'failed'|'timeout',
                'completed': {step_id: result},
                'failed': {step_id: error}
            }
        """
        try:
            results = await asyncio.wait_for(
                self._execute_workflow_internal(workflow),
                timeout=timeout
            )
            # Determine final status
            if not results["failed"]:
                results["status"] = "completed"
            elif results["completed"]:
                results["status"] = "partial"
            else:
                results["status"] = "failed"
            return results
        except asyncio.TimeoutError:
            logger.error(f"Workflow timed out after {timeout} seconds")
            return {"status": "timeout", "completed": {}, "failed": {}}

    async def _execute_workflow_internal(self, workflow: Dict) -> Dict:
        """Actual workflow implementation"""
        logger.debug(f"Starting workflow execution with {len(workflow['steps'])} steps")
        pending = {step["id"]: step for step in workflow["steps"]}
        completed = {}
        failed = {}
        context = {}

        while pending:
            logger.debug(f"Pending steps: {list(pending.keys())}")
            
            # Process conditional steps first
            conditionals = [s for s in pending.values() if "when" in s]
            for step in conditionals:
                if all(dep in completed for dep in step.get("depends_on", [])):
                    logger.debug(f"Evaluating conditional step {step['id']}")
                    condition_met = await self._evaluate_condition(step["when"], context)
                    branch_steps = step["then"] if condition_met else step.get("else", [])
                    
                    logger.debug(f"Condition {'met' if condition_met else 'not met'} for {step['id']}")
                    del pending[step["id"]]
                    for new_step in branch_steps:
                        pending[new_step["id"]] = new_step

            # Find executable steps (dependencies met, no condition)
            executable = [
                step for step in pending.values()
                if all(dep in completed for dep in step.get("depends_on", []))
                and "when" not in step
            ]

            if not executable:
                if not any(step.get("depends_on") for step in pending.values()):
                    logger.error("Workflow deadlock - no executable steps")
                    raise RuntimeError("Workflow deadlock - no executable steps")
                await asyncio.sleep(0.1)
                continue

            # Execute all eligible steps
            logger.debug(f"Executing steps: {[s['id'] for s in executable]}")
            tasks = []
            for step in executable:
                task = self._execute_workflow_step(step, completed, failed, context)
                tasks.append(asyncio.create_task(task))
                del pending[step["id"]]

            await asyncio.gather(*tasks)
            logger.debug(f"Completed batch: {[s['id'] for s in executable]}")

        logger.debug(f"Workflow completed with {len(completed)} successful steps and {len(failed)} failures")
        return {"completed": completed, "failed": failed}

    def _resolve_templates(self, input_data: Dict, context: Dict) -> Dict:
        """Replace {{variable}} with values from context"""
        resolved = {}
        for key, value in input_data.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                var_name = value[2:-2].strip()
                resolved[key] = context.get(var_name, value)
            else:
                resolved[key] = value
        return resolved

    async def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """
        Safely evaluate a workflow condition against execution context
        
        Args:
            condition: String expression to evaluate
            context: Current workflow context dictionary
            
        Returns:
            bool: True if condition evaluates truthy, False otherwise
        """
        try:
            # Restricted globals for safety
            safe_globals = {
                '__builtins__': {
                    'bool': bool,
                    'int': int,
                    'float': float,
                    'str': str,
                    'len': len,
                    'min': min,
                    'max': max
                }
            }
            return bool(eval(condition, safe_globals, context))
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False

    async def _execute_workflow_step(self, step: Dict, completed: Dict, failed: Dict, context: Dict) -> None:
        step_id = step["id"]
        agent = self.agents.get(step["agent_id"])
        
        if not agent:
            failed[step_id] = {"error": f"Agent {step['agent_id']} not found"}
            return

        try:
            # Add per-step timeout handling
            result = await asyncio.wait_for(
                agent.execute_capability(step["task"], step.get("input", {})),
                timeout=step.get("timeout", 1.0)
            )
            completed[step_id] = result
            context[step_id] = result.get("result")
        except asyncio.TimeoutError:
            failed[step_id] = {"error": f"Step timed out after {step.get('timeout', 1.0)}s"}
        except Exception as e:
            failed[step_id] = {"error": str(e)}
