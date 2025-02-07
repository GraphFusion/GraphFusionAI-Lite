class Agent:
    """
    Base class for agents in the multi-agent system.
    Handles agent behavior, communication, and memory management.
    """
    
    def __init__(self, agent_id, role, graph_manager):
        """Initialize the agent with an ID, role, and reference to the graph manager."""
        self.agent_id = agent_id
        self.role = role
        self.graph_manager = graph_manager
        self.memory = {}
        self.graph_manager.add_agent(self.agent_id, {"role": self.role})

    def communicate(self, target_agent, message):
        """Send a message to another agent by adding an interaction to the graph."""
        self.graph_manager.add_connection(self.agent_id, target_agent, relation="communicates_with")
        print(f"{self.agent_id} -> {target_agent}: {message}")

    def store_memory(self, key, value):
        """Store information in the agent's local memory."""
        self.memory[key] = value

    def recall_memory(self, key):
        """Retrieve information from the agent's local memory."""
        return self.memory.get(key, None)

# Example usage
if __name__ == "__main__":
    from graph_manager import GraphManager
    
    gm = GraphManager("graph_data.json")
    agent1 = Agent("Agent1", "planner", gm)
    agent2 = Agent("Agent2", "executor", gm)
    agent1.communicate("Agent2", "Start execution")
    agent1.store_memory("task", "Optimize pipeline")
    print(agent1.recall_memory("task"))
