import sqlite3
import json
import networkx as nx

class GraphStorage:
    """Handles persistent storage of agent graphs using SQLite."""

    def __init__(self, db_path="graph_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database schema."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS agent_graph (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                graph_json TEXT)''')
        self.conn.commit()

    def save_graph(self, graph: nx.Graph):
        """Save a NetworkX graph to the database."""
        graph_json = json.dumps(nx.node_link_data(graph))
        self.cursor.execute("INSERT INTO agent_graph (graph_json) VALUES (?)", (graph_json,))
        self.conn.commit()

    def load_graph(self) -> nx.Graph:
        """Load the most recent NetworkX graph from the database."""
        self.cursor.execute("SELECT graph_json FROM agent_graph ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        if row:
            return nx.node_link_graph(json.loads(row[0]))
        return nx.Graph()

    def close(self):
        """Close the database connection."""
        self.conn.close()

# Example usage
if __name__ == "__main__":
    storage = GraphStorage()
    G = nx.Graph()
    G.add_edge("Agent1", "Agent2", task="Data processing")
    storage.save_graph(G)
    loaded_graph = storage.load_graph()
    print("Loaded Graph Nodes:", loaded_graph.nodes())
    print("Loaded Graph Edges:", loaded_graph.edges())
    storage.close()
