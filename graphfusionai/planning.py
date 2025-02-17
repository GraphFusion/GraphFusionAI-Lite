import heapq
import time
import random
import itertools
import networkx as nx
import sqlite3

class Task:
    """Represents a task with priority, complexity, and dependencies."""
    
    def __init__(self, task_id, description, priority=1, complexity=1, dependencies=None):
        self.task_id = task_id
        self.description = description
        self.priority = priority  
        self.complexity = complexity  
        self.dependencies = dependencies if dependencies else []
        self.status = "pending"  # "pending", "in_progress", "completed", "failed"
    
    def __lt__(self, other):
        """Allows tasks to be sorted based on priority (higher first)."""
        return self.priority > other.priority  # Max heap
    
    def __repr__(self):
        return f"Task({self.task_id}, {self.description}, P={self.priority}, C={self.complexity}, Status={self.status})"

class Agent:
    """Represents an agent that executes tasks."""
    
    def __init__(self, agent_id, capacity=5):
        self.agent_id = agent_id
        self.capacity = capacity  # Max workload capacity
        self.current_load = 0  # Tracks active tasks
        self.completed_tasks = []
        self.assigned_tasks = []

    def assign_task(self, task):
        """Assigns a task if capacity allows."""
        if self.current_load < self.capacity:
            self.assigned_tasks.append(task) 
            print(f"Agent {self.agent_id} is executing: {task.description}")
            self.current_load += 1
            time.sleep(random.uniform(0.5, 1.5))  # Simulate execution
            self.complete_task(task)
        else:
            print(f"Agent {self.agent_id} is overloaded. Task '{task.description}' deferred.")

    def complete_task(self, task):
        """Marks a task as completed."""
        task.status = "completed"
        self.current_load -= 1
        self.completed_tasks.append(task)
        self.assigned_tasks.remove(task)  
        print(f"Agent {self.agent_id} completed task: {task.description}")

class TaskPlanner:
    """Handles task allocation, planning, and persistence."""
    
    def __init__(self, strategy="priority", db_path="tasks.db"):
        """
        Strategies:
        - "fifo": First In, First Out
        - "priority": Highest-priority first
        - "adaptive": Dynamic task allocation
        """
        self.strategy = strategy
        self.task_queue = []  
        self.pending_tasks = []  # ⬅ **NEW**: Holds tasks waiting for dependencies
        self.agents = {}  
        self.agent_cycle = None  # Round-robin iterator
        self.task_graph = nx.DiGraph()  
        self.db_path = db_path
        self._setup_db()

    def _setup_db(self):
        """Initialize SQLite database for task logging."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_log (
                task_id TEXT PRIMARY KEY,
                description TEXT,
                priority INTEGER,
                complexity INTEGER,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_agent(self, agent_id, capacity=5):
        """Register a new agent."""
        self.agents[agent_id] = Agent(agent_id, capacity)
        self.agent_cycle = itertools.cycle(self.agents.values())  # Round-robin agent selection

    def add_task(self, task):
        """Add a new task and log it."""
        self.task_graph.add_node(task.task_id, task=task)

        for dep in task.dependencies:
            if dep in self.task_graph:
                self.task_graph.add_edge(dep, task.task_id)
        
        if self.strategy == "fifo":
            self.task_queue.append(task)  
        else:
            heapq.heappush(self.task_queue, task)  

        self._log_task(task)
        print(f"Task added: {task}")

    def _log_task(self, task):
        """Store task info in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO task_log VALUES (?, ?, ?, ?, ?)", 
                       (task.task_id, task.description, task.priority, task.complexity, task.status))
        conn.commit()
        conn.close()

    def assign_tasks(self):
        """Allocate tasks to agents fairly."""
        while self.task_queue or self.pending_tasks:
            # Process pending tasks first
            if self.pending_tasks:
                print("Retrying pending tasks...")
                self.task_queue.extend(self.pending_tasks)
                self.pending_tasks.clear()

            # Process the queue
            while self.task_queue:
                task = heapq.heappop(self.task_queue)

                # Ensure dependencies are met before assignment
                if not self.resolve_dependencies(task.task_id):
                    print(f"Task {task.task_id} waiting for dependencies.")
                    self.pending_tasks.append(task)  # Store in pending queue
                    continue

                self._assign_task_to_agent(task)

    def _assign_task_to_agent(self, task):
        """Assigns tasks using a round-robin approach."""
        available_agents = [agent for agent in self.agents.values() if agent.current_load < agent.capacity]

        if available_agents:
            best_agent = next(self.agent_cycle)  # Round-robin selection
            best_agent.assign_task(task)
            task.status = "in_progress"
            self._log_task(task)
        else:
            print(f"No available agents for task: {task.description}. Retrying later.")
            self.pending_tasks.append(task)  # Store in pending queue for later

    def resolve_dependencies(self, task_id):
        """Checks if task dependencies are met before execution."""
        if task_id in self.task_graph:
            for dependency in list(self.task_graph.predecessors(task_id)):
                dep_task = self.task_graph.nodes[dependency]['task']
                if dep_task.status != "completed":
                    return False
        return True
    
    def shutdown(self):
        """Shutdown and save state."""
        print("Shutting down TaskPlanner...")
        for agent in self.agents.values():
            print(f"Agent {agent.agent_id} completed {len(agent.completed_tasks)} tasks.")

# Example Usage
if __name__ == "__main__":
    planner = TaskPlanner(strategy="priority")

    # Register Agents
    planner.add_agent("Agent1", capacity=3)
    planner.add_agent("Agent2", capacity=2)

    # Add Tasks with Dependencies
    planner.add_task(Task("T1", "Data Collection", priority=5, complexity=2))
    planner.add_task(Task("T2", "Data Preprocessing", priority=4, complexity=3, dependencies=["T1"]))
    planner.add_task(Task("T3", "Feature Engineering", priority=4, complexity=3, dependencies=["T2"]))
    planner.add_task(Task("T4", "Model Training", priority=6, complexity=5, dependencies=["T3"]))
    planner.add_task(Task("T5", "Model Evaluation", priority=3, complexity=2, dependencies=["T4"]))
    planner.add_task(Task("T6", "Hyperparameter Tuning", priority=7, complexity=5, dependencies=["T4"]))
    planner.add_task(Task("T7", "Final Model Deployment", priority=8, complexity=4, dependencies=["T5", "T6"]))

    # Assign Tasks
    planner.assign_tasks()

    # Shutdown
    planner.shutdown()
