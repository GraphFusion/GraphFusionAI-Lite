import os
import sys
import time
import random
from graphfusionai.planning import TaskPlanner, Task
from graphfusionai.distributed import DistributedExecutor

def execute_task_with_monitoring(agent_id, task, planner):
    """Executes a task with logging and failure handling."""
    print(f"[START] Agent {agent_id} executing task: {task.description}")

    try:
        execution_time = random.uniform(1, 3)  # Simulating execution time
        time.sleep(execution_time)
        
        if random.random() < 0.1:  # Simulating failure (10% chance)
            raise Exception(f"Simulated failure for task {task.task_id}")

        task.status = "completed"
        print(f"[SUCCESS] Agent {agent_id} completed task: {task.description}")

    except Exception as e:
        print(f"[ERROR] Task {task.task_id} failed: {e}")
        planner.reassign_failed_tasks([task])  # Retrying failed tasks

if __name__ == "__main__":
    # Initializing Task Planner & Distributed Executor
    planner = TaskPlanner(strategy="priority")
    executor = DistributedExecutor(mode="hybrid", remote_nodes=[("127.0.0.1", 5000)])

    # Registering Agents
    planner.add_agent("Agent1", capacity=3)
    planner.add_agent("Agent2", capacity=2)

    # Defining Tasks with Dependencies
    tasks = [
        Task("T1", "Data Collection", priority=5, complexity=2),
        Task("T2", "Data Preprocessing", priority=4, complexity=3, dependencies=["T1"]),
        Task("T3", "Feature Engineering", priority=4, complexity=3, dependencies=["T2"]),
        Task("T4", "Model Training", priority=6, complexity=5, dependencies=["T3"]),
        Task("T5", "Model Evaluation", priority=3, complexity=2, dependencies=["T4"]),
        Task("T6", "Hyperparameter Tuning", priority=7, complexity=5, dependencies=["T4"]),
        Task("T7", "Final Model Deployment", priority=8, complexity=4, dependencies=["T5", "T6"]),
    ]

    # Adding Tasks to Planner
    for task in tasks:
        planner.add_task(task)

    # Assigning and Executing Tasks
    planner.assign_tasks()
    for agent_id, agent in planner.agents.items():
        for task in agent.completed_tasks:
            executor.execute_task(agent_id, task.description, task_type="light" if task.complexity < 3 else "heavy")

    planner.shutdown()
    executor.shutdown()
