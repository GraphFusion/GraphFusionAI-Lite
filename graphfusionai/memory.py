import json
import threading

class MemoryManager:
    """
    Manages both local and shared memory for agents.
    Supports persistence, retrieval, and selective memory retention.
    """
    
    def __init__(self, memory_file="memory.json"):
        """Initialize memory manager with optional disk-based storage."""
        self.memory_file = memory_file
        self.lock = threading.Lock()
        self.local_memory = {}  # Per-agent memory
        self.shared_memory = self.load_memory()

    def store_local(self, agent_id, key, value):
        """Store key-value pair in an agent's local memory."""
        if agent_id not in self.local_memory:
            self.local_memory[agent_id] = {}
        self.local_memory[agent_id][key] = value

    def recall_local(self, agent_id, key):
        """Retrieve a value from an agent's local memory."""
        return self.local_memory.get(agent_id, {}).get(key, None)

    def store_shared(self, key, value, persistent=True):
        """Store key-value pair in the shared global memory."""
        with self.lock:
            self.shared_memory[key] = value
            if persistent:
                self.save_memory()

    def recall_shared(self, key):
        """Retrieve a value from the shared global memory."""
        return self.shared_memory.get(key, None)

    def save_memory(self):
        """Persist shared memory to disk."""
        with self.lock:
            with open(self.memory_file, "w") as f:
                json.dump(self.shared_memory, f, indent=4)

    def load_memory(self):
        """Load shared memory from disk if available."""
        try:
            with open(self.memory_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def selective_memory_retention(self, keys_to_keep):
        """Retain only specified keys in shared memory, clearing the rest."""
        with self.lock:
            self.shared_memory = {key: self.shared_memory[key] for key in keys_to_keep if key in self.shared_memory}
            self.save_memory()

# Example usage
if __name__ == "__main__":
    memory = MemoryManager()
    memory.store_local("Agent1", "task", "Analyze data")
    print(memory.recall_local("Agent1", "task"))
    memory.store_shared("global_strategy", "Collaborative filtering")
    print(memory.recall_shared("global_strategy"))
    memory.selective_memory_retention(["global_strategy"])
