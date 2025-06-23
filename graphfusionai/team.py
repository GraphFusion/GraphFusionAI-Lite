import threading
from typing import Dict, List, Any, Optional
from .agent import Agent

class Team:
    """
    Represents a team of agents that collaborate to achieve common goals.
    Handles task assignment, communication, and workflow execution.
    
    Attributes:
        team_id: Unique identifier for the team
        agents: Dictionary of agents in the team
        task_queue: Queue of tasks to be assigned
        communication_graph: Representation of communication channels
        shared_state: Shared state accessible to all agents
    """
    
    def __init__(self, team_id: str, graph_manager):
        self.team_id = team_id
        self.agents: Dict[str, Agent] = {}
        self.task_queue = []
        self.communication_graph = {}
        self.shared_state = {}
        self.graph_manager = graph_manager
        self.lock = threading.Lock()
        
        # Register team in knowledge graph
        self.graph_manager.add_node(self.team_id, {"type": "team"})
    
    def add_agent(self, agent: Agent):
        """Add an agent to the team"""
        with self.lock:
            self.agents[agent.agent_id] = agent
            agent.assign_to_team(self)
            # Initialize communication graph entry
            self.communication_graph[agent.agent_id] = []
            
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
    
    def send_message(self, sender_id: str, recipient_id: str, message: Dict):
        """Send a message from one agent to another"""
        if recipient_id not in self.agents:
            raise ValueError(f"Recipient agent {recipient_id} not found")
        
        # Update communication graph
        if sender_id not in self.communication_graph:
            self.communication_graph[sender_id] = []
        if recipient_id not in self.communication_graph[sender_id]:
            self.communication_graph[sender_id].append(recipient_id)
        
        # Deliver message
        self.agents[recipient_id].receive_message(sender_id, message)
    
    def report_task_completion(self, agent_id: str, task: Dict, result: Any):
        """Handle task completion report"""
        # Update shared state or knowledge graph
        self.graph_manager.add_knowledge(agent_id, task["type"], result)
        
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
