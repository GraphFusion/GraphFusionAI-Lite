import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from graphfusionai.memory import MemoryManager
from graphfusionai.execution import TaskExecutor
from graphfusionai.monitor import AgentMonitor
from graphfusionai.fault_tolerance import FaultTolerance

# Initialize components
memory = MemoryManager()
executor = TaskExecutor()
monitor = AgentMonitor()
fault_tolerance = FaultTolerance()

# Example agent workflow
def agent_workflow(agent_id, task, delegate_to=None):
    monitor.log_activity(agent_id, f"Starting task: {task}")
    
    if delegate_to:
        monitor.log_activity(agent_id, f"Delegating task '{task}' to {delegate_to}")
        executor.execute_task(delegate_to, task)
        return
    
    try:
        executor.execute_task(agent_id, task)
        memory.store_local(agent_id, "last_task", task)
        monitor.log_activity(agent_id, f"Completed task: {task}")
    except Exception as e:
        monitor.log_activity(agent_id, f"Task failed: {task}, Error: {e}")
        fault_tolerance.retry_task(task, agent_id)
        fault_tolerance.recover_agent(agent_id)

# Multi-agent collaboration example
def collaborative_workflow():
    agent_workflow("Agent1", "Data preprocessing")
    agent_workflow("Agent2", "Model training", delegate_to="Agent3")
    agent_workflow("Agent3", "Model evaluation")

# Run example
if __name__ == "__main__":
    collaborative_workflow()