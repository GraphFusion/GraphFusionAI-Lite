import threading
from typing import Dict, List, Callable, Any, Optional

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
                 graph_manager, team=None):
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities
        self.team = team
        self.graph_manager = graph_manager
        self.memory = {}
        self.task_queue = []
        
        # Register agent in knowledge graph
        self.graph_manager.add_agent(self.agent_id, {"role": self.role})

    def assign_to_team(self, team):
        """Assign this agent to a team"""
        self.team = team
        self.graph_manager.add_connection(self.agent_id, team.team_id, 
                                         relation="member_of")

    def add_capability(self, name: str, function: Callable):
        """Add a new capability to the agent"""
        self.capabilities[name] = function

    def execute_task(self, task: Dict):
        """Execute a task using the agent's capabilities"""
        if task["type"] not in self.capabilities:
            raise ValueError(f"Agent {self.agent_id} lacks capability: {task['type']}")
            
        try:
            result = self.capabilities[task["type"]](**task["parameters"])
            self.team.report_task_completion(self.agent_id, task, result)
            return result
        except Exception as e:
            self.team.report_task_failure(self.agent_id, task, str(e))
            raise

    def request_help(self, task: Dict[str, Any], recipient_id: str):
        """Request help from another agent for a specific task"""
        if not isinstance(recipient_id, str):
            raise TypeError(f"recipient_id must be a string, got {type(recipient_id)}: {recipient_id}")
        if not self.team:
            raise RuntimeError("Agent not part of a team")
        self.team.send_message(self.agent_id, recipient_id, {
            "type": "help_request",
            "task": task
        })

    def send_message(self, recipient_id: str, content: Dict):
        """Send a message to another agent"""
        if not self.team:
            raise RuntimeError("Agent not part of a team")
        self.team.send_message(self.agent_id, recipient_id, content)

    def receive_message(self, sender_id: str, content: Dict):
        """Handle incoming message"""
        # Default implementation - can be overridden
        print(f"{self.agent_id} received message from {sender_id}: {content}")
        
        if content["type"] == "help_request":
            # Automatically accept help requests
            self.execute_task(content["task"])

    def store_memory(self, key: str, value: Any):
        """Store information in local memory"""
        self.memory[key] = value

    def recall_memory(self, key: str) -> Optional[Any]:
        """Retrieve information from local memory"""
        return self.memory.get(key, None)

    def contribute_to_knowledge_graph(self, key: str, value: Any):
        """Contribute knowledge to the shared graph"""
        self.graph_manager.add_knowledge(self.agent_id, key, value)

# Example usage
if __name__ == "__main__":
    from graph_manager import GraphManager
    
    gm = GraphManager("graph_data.json")
    agent1 = Agent("Agent1", "planner", {}, gm)
    agent2 = Agent("Agent2", "executor", {}, gm)
    agent1.assign_to_team(None)  # Assign to a team
    agent2.assign_to_team(None)  # Assign to a team
    agent1.send_message("Agent2", {"type": "help_request", "task": {"type": "data_processing"}})
    agent1.store_memory("task", "Optimize pipeline")
    print(agent1.recall_memory("task"))
    agent1.contribute_to_knowledge_graph("strategy", "Divide and conquer")
    # print(agent1.retrieve_global_knowledge("strategy"))  # This method does not exist in the new Agent class
    # agent2.execute_task("Data processing")  # This method requires a task dictionary in the new Agent class
