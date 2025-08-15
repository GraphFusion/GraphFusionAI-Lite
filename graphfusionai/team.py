import threading
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional
from .agent import Agent
from .graph_manager import GraphManager
from .persistence import TeamStateDB, TeamState

logger = logging.getLogger(__name__)

class Team:
    """
    Represents a team of agents that collaborate to achieve common goals.
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
        self.agents: Dict[str, Agent] = {}
        self.task_queue: List[Dict] = []
        self.communication_graph: Dict[str, List[str]] = {}
        self.shared_state: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.state_db = state_db
        self.auto_save_interval = auto_save_interval
        self._auto_save_task: Optional[asyncio.Task] = None

        self.graph_manager.add_agent(self.team_id, {"type": "team"})

        if state_db:
            self.load_state()

    # -------------------------------------------------------------------------
    # Agent Management
    # -------------------------------------------------------------------------
    async def add_agent(self, agent: Agent):
        """Add an agent to the team."""
        with self.lock:
            self.agents[agent.agent_id] = agent
            agent.team = self
            self.graph_manager.add_agent(agent.agent_id, {"role": agent.role})
            self.graph_manager.add_connection(agent.agent_id, self.team_id, "member")

    def remove_agent(self, agent_id: str):
        """Remove an agent from the team."""
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                if agent_id in self.communication_graph:
                    del self.communication_graph[agent_id]
                for connections in self.communication_graph.values():
                    if agent_id in connections:
                        connections.remove(agent_id)

    def get_agent_by_role(self, role: str) -> Optional[Agent]:
        """Find an agent by role."""
        return next((a for a in self.agents.values() if a.role == role), None)

    # -------------------------------------------------------------------------
    # Task Management
    # -------------------------------------------------------------------------
    def add_task(self, task: Dict):
        """Add a task to the team's queue."""
        with self.lock:
            self.task_queue.append(task)

    async def assign_task(
        self,
        agent_id: str,
        task: Dict,
        priority: str = "normal",
        timeout: int = 60
    ) -> Any:
        """Assign a task to an agent with timeout handling."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found in team")

        try:
            return await asyncio.wait_for(
                agent.execute_task(task, priority),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Task timeout: {task.get('task_id')} for agent {agent_id}")
            raise

    def report_task_completion(self, agent_id: str, task: Dict, result: Any):
        """Handle task completion report."""
        self.graph_manager.add_knowledge(
            agent_id, task["type"], result, knowledge_type=task["type"]
        )

    def report_task_failure(self, agent_id: str, task: Dict, error: str):
        """Handle task failure report."""
        logger.error(f"Task {task} failed: {error}")
        self.add_task(task)  # Requeue for retry

    # -------------------------------------------------------------------------
    # Messaging
    # -------------------------------------------------------------------------
    def broadcast(self, sender_id: str, message: Dict):
        """Broadcast a message to all agents in the team."""
        for agent_id in self.agents:
            if agent_id != sender_id:
                asyncio.create_task(self.send_message(sender_id, agent_id, message))

    async def send_message(self, sender_id: str, recipient_id: str, content: Dict):
        """Send a message from one agent to another."""
        logger.debug(f"Sending message from {sender_id} to {recipient_id}")
        if recipient_id not in self.agents:
            raise ValueError(f"Recipient agent {recipient_id} not found in team")

        self.graph_manager.add_communication(sender_id, recipient_id, content)
        await self.agents[recipient_id].receive_message(sender_id, content)

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------
    def load_state(self):
        """Load team state from database."""
        if self.state_db:
            state = self.state_db.load_state(self.team_id)
            if state:
                self.task_queue = state.task_queue

    async def save_state(self):
        """Save current team state to database."""
        if self.state_db:
            state = TeamState(
                team_id=self.team_id,
                agent_ids=list(self.agents.keys()),
                task_queue=self.task_queue,
                last_updated=time.time()
            )
            self.state_db.save_state(state)

    async def start(self):
        """Start background tasks for the team."""
        if self.auto_save_interval > 0 and self._auto_save_task is None:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())
            logger.info(f"Team {self.team_id} auto-save started.")

    async def stop(self):
        """Stop background tasks for the team."""
        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
            self._auto_save_task = None
            logger.info(f"Team {self.team_id} auto-save stopped.")

    async def _auto_save_loop(self):
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

    # -------------------------------------------------------------------------
    # Workflow Execution with Conditionals, Parallelism, and Templates
    # -------------------------------------------------------------------------
    async def execute_workflow(self, workflow: Dict, timeout: Optional[int] = None) -> Dict:
        """Execute a workflow with support for conditionals, parallel steps, templates, and timeouts."""
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
            return {"status": "timeout", "completed": {}, "failed": {}}

    async def _execute_workflow_internal(self, workflow: Dict) -> Dict:
        pending = {step["id"]: step for step in workflow["steps"]}
        completed, failed, context = {}, {}, {}

        while pending:
            # Handle conditionals
            for step in [s for s in list(pending.values()) if "when" in s]:
                if all(dep in completed for dep in step.get("depends_on", [])):
                    condition_met = await self._evaluate_condition(step["when"], context)
                    branch_steps = step["then"] if condition_met else step.get("else", [])
                    del pending[step["id"]]
                    for new_step in branch_steps:
                        pending[new_step["id"]] = new_step

            # Executable steps
            executable = [
                s for s in list(pending.values())
                if all(dep in completed for dep in s.get("depends_on", []))
                and "when" not in s
            ]

            if not executable:
                if not any(s.get("depends_on") for s in pending.values()):
                    raise RuntimeError("Workflow deadlock - no executable steps")
                await asyncio.sleep(0.1)
                continue

            parallel_steps = [s for s in executable if s.get("parallel", False)]
            serial_steps = [s for s in executable if not s.get("parallel", False)]

            if parallel_steps:
                tasks = [
                    asyncio.create_task(self._execute_workflow_step(s, completed, failed, context))
                    for s in parallel_steps
                ]
                for s in parallel_steps:
                    del pending[s["id"]]
                await asyncio.gather(*tasks, return_exceptions=True)

            for s in serial_steps:
                await self._execute_workflow_step(s, completed, failed, context)
                del pending[s["id"]]

        return {"completed": completed, "failed": failed}

    async def _execute_workflow_step(self, step: Dict, completed: Dict, failed: Dict, context: Dict):
        step_id = step["id"]
        agent = self.agents.get(step["agent_id"])
        if not agent:
            failed[step_id] = {"error": f"Agent {step['agent_id']} not found"}
            return
        try:
            resolved_input = self._resolve_templates(step.get("input", {}), context)
            result = await self.assign_task(
                step["agent_id"],
                {
                    "task_id": step_id,
                    "description": f"Workflow step: {step_id}",
                    **resolved_input
                },
                timeout=step.get("timeout", 60)
            )
            completed[step_id] = result
            context[step_id] = result.get("result")
        except asyncio.TimeoutError:
            failed[step_id] = {"error": f"Step timed out after {step.get('timeout', 60)}s"}
        except Exception as e:
            failed[step_id] = {"error": str(e)}

    def _resolve_templates(self, input_data: Dict, context: Dict) -> Dict:
        """Replace {{variable}} placeholders from context."""
        resolved = {}
        for key, value in input_data.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                var_name = value[2:-2].strip()
                resolved[key] = context.get(var_name, value)
            else:
                resolved[key] = value
        return resolved

    async def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """Evaluate a simple Python expression as condition."""
        try:
            return bool(eval(condition, {}, context))
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
