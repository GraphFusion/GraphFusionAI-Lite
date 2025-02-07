import threading

class Agent:
    """
    Base class for agents in the multi-agent system.
    Handles agent behavior, communication, memory management, task execution, and fault tolerance.
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
    
    def contribute_to_global_knowledge(self, key, value):
        """Store information in the shared global knowledge graph."""
        self.graph_manager.graph.nodes[self.agent_id][key] = value

    def retrieve_global_knowledge(self, key):
        """Retrieve information from the shared global knowledge graph."""
        return self.graph_manager.graph.nodes[self.agent_id].get(key, None)
    
    def execute_task(self, task):
        """Execute a task in a separate thread with fault tolerance."""
        def task_wrapper():
            try:
                print(f"{self.agent_id} ({self.role}) is executing: {task}")
                # Simulated task execution (extend with real logic)
            except Exception as e:
                print(f"Error executing task {task} by {self.agent_id}: {e}")
                self.retry_task(task)
        
        task_thread = threading.Thread(target=task_wrapper)
        task_thread.start()
    
    def retry_task(self, task, retries=3):
        """Retry a failed task up to a specified number of times."""
        for attempt in range(retries):
            try:
                print(f"Retrying {task}, attempt {attempt + 1}...")
                self.execute_task(task)
                return
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
        print(f"Task {task} failed after {retries} attempts.")
    
# Example usage
if __name__ == "__main__":
    from graph_manager import GraphManager
    
    gm = GraphManager("graph_data.json")
    agent1 = Agent("Agent1", "planner", gm)
    agent2 = Agent("Agent2", "executor", gm)
    agent1.communicate("Agent2", "Start execution")
    agent1.store_memory("task", "Optimize pipeline")
    print(agent1.recall_memory("task"))
    agent1.contribute_to_global_knowledge("strategy", "Divide and conquer")
    print(agent1.retrieve_global_knowledge("strategy"))
    agent2.execute_task("Data processing")
