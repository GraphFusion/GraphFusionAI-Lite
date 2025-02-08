import multiprocessing
import threading
import queue
import socket
import pickle
import time

class DistributedExecutor:
    """Handles distributed execution of agent tasks using multi-threading, multi-processing, and remote execution."""
    
    def __init__(self, mode="hybrid", remote_nodes=None):
        """Initialize the distributed execution system.
        Modes:
        - "threading": Uses multi-threading for lightweight tasks.
        - "multiprocessing": Uses multiprocessing for heavy computations.
        - "hybrid": Uses both based on task type.
        - "distributed": Distributes tasks to remote nodes.
        """
        self.mode = mode
        self.task_queue = queue.Queue()
        self.pool = multiprocessing.Pool()
        self.threads = []
        self.remote_nodes = remote_nodes if remote_nodes else []
        self.failed_tasks = []

    def execute_task(self, agent_id, task, task_type="light"):
        """Execute a task based on the configured execution mode."""
        if self.mode == "threading" or (self.mode == "hybrid" and task_type == "light"):
            thread = threading.Thread(target=self._run_task, args=(agent_id, task))
            thread.start()
            self.threads.append(thread)
        elif self.mode == "multiprocessing" or (self.mode == "hybrid" and task_type == "heavy"):
            self.pool.apply_async(self._run_task, args=(agent_id, task), error_callback=self._handle_failure)
        elif self.mode == "distributed":
            self._send_task_to_remote(agent_id, task)
        else:
            raise ValueError("Invalid execution mode")
    
    def _run_task(self, agent_id, task):
        """Simulated task execution (to be customized per agent task logic)."""
        print(f"Agent {agent_id} executing task: {task}")
        time.sleep(1)  # Simulate task processing time
        print(f"Agent {agent_id} completed task: {task}")
    
    def _send_task_to_remote(self, agent_id, task):
        """Send task to a remote node for execution."""
        if not self.remote_nodes:
            print("No remote nodes available.")
            return
        node = self.remote_nodes[0]  # Simple round-robin strategy
        host, port = node
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                data = pickle.dumps((agent_id, task))
                s.sendall(data)
        except Exception as e:
            print(f"Failed to send task to remote node {node}: {e}")
            self.failed_tasks.append((agent_id, task))
    
    def _handle_failure(self, error):
        """Handle task execution failures."""
        print(f"Task failed due to: {error}")
    
    def retry_failed_tasks(self):
        """Retry all previously failed tasks."""
        for agent_id, task in self.failed_tasks:
            print(f"Retrying task for Agent {agent_id}: {task}")
            self.execute_task(agent_id, task)
        self.failed_tasks.clear()
    
    def shutdown(self):
        """Shutdown all running threads and processes."""
        for thread in self.threads:
            thread.join()
        self.pool.close()
        self.pool.join()

# Example usage
if __name__ == "__main__":
    remote_nodes = [("127.0.0.1", 5000)]  # Example remote node
    executor = DistributedExecutor(mode="hybrid", remote_nodes=remote_nodes)
    executor.execute_task("Agent1", "Data Processing", task_type="light")
    executor.execute_task("Agent2", "Model Training", task_type="heavy")
    executor.retry_failed_tasks()
    executor.shutdown()
