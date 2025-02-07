import threading
import time

class TaskExecutor:
    """
    Handles task execution with multi-threading, fault tolerance, and task delegation.
    Supports retries and execution logging.
    """
    
    def __init__(self, max_retries=3):
        """Initialize the task executor with configurable retry limits."""
        self.max_retries = max_retries

    def execute_task(self, agent_id, task, delegate_to=None):
        """Execute a task, either directly or by delegating it to another agent."""
        if delegate_to:
            print(f"{agent_id} delegating task '{task}' to {delegate_to}")
            return
        
        def task_wrapper():
            for attempt in range(1, self.max_retries + 1):
                try:
                    print(f"{agent_id} executing task: {task}")
                    time.sleep(1)  # Simulated task execution
                    print(f"{agent_id} successfully completed task: {task}")
                    return
                except Exception as e:
                    print(f"Error executing task {task} by {agent_id}, attempt {attempt}: {e}")
            print(f"{agent_id} failed to complete task {task} after {self.max_retries} attempts.")
        
        task_thread = threading.Thread(target=task_wrapper)
        task_thread.start()

# Example usage
if __name__ == "__main__":
    executor = TaskExecutor()
    executor.execute_task("Agent1", "Data processing")
    executor.execute_task("Agent2", "Model training", delegate_to="Agent3")
