import networkx as nx
import json

class GraphManager:
    """
    Manages the shared knowledge graph using NetworkX.
    Handles agent nodes, relationships, and persistence.
    """
    
    def __init__(self, persistent_storage=None):
        """Initialize the graph manager with an optional persistent storage file."""
        self.graph = nx.DiGraph()
        self.persistent_storage = persistent_storage
        if self.persistent_storage:
            self.load_graph()

    def add_agent(self, agent_id, attributes=None):
        """Add a new agent (node) to the graph with optional attributes."""
        if attributes is None:
            attributes = {}
        self.graph.add_node(agent_id, **attributes)
    
    def remove_agent(self, agent_id):
        """Remove an agent (node) from the graph."""
        if agent_id in self.graph:
            self.graph.remove_node(agent_id)
    
    def add_connection(self, source_agent, target_agent, weight=1, relation="communicates_with"):
        """Add a directed connection (edge) between two agents with an optional weight and relation type."""
        if source_agent in self.graph and target_agent in self.graph:
            self.graph.add_edge(source_agent, target_agent, weight=weight, relation=relation)
    
    def remove_connection(self, source_agent, target_agent):
        """Remove a connection (edge) between two agents."""
        if self.graph.has_edge(source_agent, target_agent):
            self.graph.remove_edge(source_agent, target_agent)
    
    def get_neighbors(self, agent_id):
        """Retrieve a list of agents directly connected to a given agent."""
        return list(self.graph.successors(agent_id))
    
    def save_graph(self):
        """Save the graph to a file in JSON format."""
        if self.persistent_storage:
            data = nx.node_link_data(self.graph)
            with open(self.persistent_storage, 'w') as f:
                json.dump(data, f)
    
    def load_graph(self):
        """Load the graph from a JSON file if persistence is enabled."""
        try:
            with open(self.persistent_storage, 'r') as f:
                data = json.load(f)
                self.graph = nx.node_link_graph(data)
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Ignore errors if the file does not exist or is corrupted
    
    def visualize_graph(self):
        """Generate a simple visualization of the graph (for debugging)."""
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000)
        plt.show()

# Example usage
if __name__ == "__main__":
    gm = GraphManager("graph_data.json")
    gm.add_agent("Agent1", {"role": "planner"})
    gm.add_agent("Agent2", {"role": "executor"})
    gm.add_connection("Agent1", "Agent2", relation="delegates_task")
    gm.save_graph()
    gm.visualize_graph()
