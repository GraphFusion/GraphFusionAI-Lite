import heapq
import time
import random
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
        """Allows tasks to be sorted based on priority."""
        return self.priority > other.priority  # Max heap (higher priority first)
    
    def __repr__(self):
        return f"Task({self.task_id}, {self.description}, P={self.priority}, C={self.complexity}, Status={self.status})"

class Agent:
    """Represents an agent that executes tasks."""
    
    def __init__(self, agent_id, capacity=5):
        self.agent_id = agent_id
        self.capacity = capacity  # Maximum workload capacity
        self.current_load = 0  # Tracks the number of ongoing tasks
        self.completed_tasks = []
        self.assigned_tasks = []  # ✅ Add this to track assigned tasks

    def assign_task(self, task):
        """Assign a new task if capacity allows."""
        if self.current_load < self.capacity:
            self.assigned_tasks.append(task) 
            print(f"Agent {self.agent_id} is executing: {task.description}")
            self.current_load += 1
            time.sleep(random.uniform(0.5, 1.5))  # Simulate task execution
            self.complete_task(task)
        else:
            print(f"Agent {self.agent_id} is overloaded. Task '{task.description}' deferred.")

    def complete_task(self, task):
        """Mark a task as completed."""
        task.status = "completed"
        self.current_load -= 1
        self.completed_tasks.append(task)
        self.assigned_tasks.remove(task)  # ✅ Remove task after completion
        print(f"Agent {self.agent_id} completed task: {task.description}")

class TaskPlanner:
    """Handles task allocation, planning, and persistence."""
    
    def __init__(self, strategy="priority", db_path="tasks.db"):
        """
        Planning strategies:
        - "fifo": First In, First Out task execution.
        - "priority": Executes highest-priority tasks first.
        - "adaptive": Adjusts execution order dynamically based on agent workload.
        """
        self.strategy = strategy
        self.task_queue = []  # Heap queue for priority-based execution
        self.agents = {}  # Maps agent_id -> Agent instance
        self.task_graph = nx.DiGraph()  # Graph for dependency management
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
    
    def add_task(self, task):
        """Add a new task and log it to the database."""
        self.task_graph.add_node(task.task_id, task=task)

        for dep in task.dependencies:
            if dep in self.task_graph:
                self.task_graph.add_edge(dep, task.task_id)
        
        if self.strategy == "fifo":
            self.task_queue.append(task)  # Simple queue (FIFO)
        else:
            heapq.heappush(self.task_queue, task)  # Priority queue
        
        self._log_task(task)
        print(f"Task added: {task}")

    def _log_task(self, task):
        """Store task information in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO task_log VALUES (?, ?, ?, ?, ?)", 
                       (task.task_id, task.description, task.priority, task.complexity, task.status))
        conn.commit()
        conn.close()

    def assign_tasks(self):
        """Allocate tasks to agents based on the selected strategy."""
        if self.strategy == "fifo":
            random.shuffle(self.task_queue)  # To avoid bias
            for task in self.task_queue:
                self._assign_task_to_least_loaded_agent(task)
        else:
            while self.task_queue:
                task = heapq.heappop(self.task_queue)
                self._assign_task_to_least_loaded_agent(task)

    def _assign_task_to_least_loaded_agent(self, task):
        """Finds the least-loaded agent and assigns the task."""
        available_agents = [agent for agent in self.agents.values() if agent.current_load < agent.capacity]
        if available_agents:
            best_agent = min(available_agents, key=lambda a: a.current_load)
            best_agent.assign_task(task)
            task.status = "in_progress"
            self._log_task(task)
        else:
            print(f"No available agents for task: {task.description}. Retrying later.")
            self.add_task(task)  # Re-add to queue for later execution

    def reassign_failed_tasks(self, failed_tasks):
        """Reassign failed tasks."""
        print("Reassigning failed tasks...")
        for task in failed_tasks:
            task.status = "pending"  # Reset status
            self._log_task(task)
            self.add_task(task)
        self.assign_tasks()

    def resolve_dependencies(self, task_id):
        """Checks if a task's dependencies are met before execution."""
        if task_id in self.task_graph:
            for dependency in list(self.task_graph.predecessors(task_id)):
                dep_task = self.task_graph.nodes[dependency]['task']
                if dep_task.status != "completed":
                    return False
        return True
    
    def assigned_tasks(self):
        """Returns the list of currently assigned tasks."""
        return [task for task in self.task_queue if task.status == "in_progress"]

    def shutdown(self):
        """Shutdown all active tasks and save state."""
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
    planner.add_task(Task("T1", "Data Preprocessing", priority=3, complexity=2))
    planner.add_task(Task("T2", "Model Training", priority=5, complexity=4, dependencies=["T1"]))
    planner.add_task(Task("T3", "Evaluation", priority=2, complexity=1, dependencies=["T2"]))
    planner.add_task(Task("T4", "Report Generation", priority=4, complexity=2, dependencies=["T3"]))

    # Assign Tasks
    planner.assign_tasks()

    # Shutdown
    planner.shutdown()
