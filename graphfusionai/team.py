import threading
from typing import Dict, List, Any, Optional
import logging
from .agent import Agent
from .graph_manager import GraphManager

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
    
    def __init__(self, team_id: str, graph_manager: GraphManager):
        self.team_id = team_id
        self.graph_manager = graph_manager
        self.agents = {}  # Dictionary of agent_id to Agent
        self.task_queue = []
        self.communication_graph = {}
        self.shared_state = {}
        self.lock = threading.Lock()
        
        # Register the team in the knowledge graph
        self.graph_manager.add_agent(self.team_id, {"type": "team"})
    
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
    
    def assign_task(self, agent_id: str, task: Dict):
        """Assign a specific task to an agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not in team")
        self.agents[agent_id].task_queue.append(task)
    
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
