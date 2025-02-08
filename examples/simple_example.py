import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from memory import MemoryManager
from execution import TaskExecutor
from monitor import AgentMonitor
from fault_tolerance import FaultTolerance

# Initialize components
memory = MemoryManager()
executor = TaskExecutor()
monitor = AgentMonitor()
fault_tolerance = FaultTolerance()

# Example agent workflow
def agent_workflow(agent_id, task):
    monitor.log_activity(agent_id, f"Starting task: {task}")
    
    try:
        executor.execute_task(agent_id, task)
        memory.store_local(agent_id, "last_task", task)
        monitor.log_activity(agent_id, f"Completed task: {task}")
    except Exception as e:
        monitor.log_activity(agent_id, f"Task failed: {task}, Error: {e}")
        fault_tolerance.retry_task(task, agent_id)
        fault_tolerance.recover_agent(agent_id)

# Run example
if __name__ == "__main__":
    agent_workflow("Agent1", "Data processing")
