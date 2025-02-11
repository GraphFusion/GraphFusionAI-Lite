import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import time
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
from graphfusionai.planning import TaskPlanner, Task
from graphfusionai.distributed import DistributedExecutor

# Ensure correct import paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Define the DQN Model
class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, output_dim)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

# Define the RL Agent
class RLAgent:
    def __init__(self, state_dim, action_dim, lr=0.001, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.memory = deque(maxlen=10000)
        self.model = DQN(state_dim, action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
    
    def select_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return torch.argmax(q_values).item()
    
    def store_experience(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def train(self, batch_size=32):
        if len(self.memory) < batch_size:
            return
        batch = random.sample(self.memory, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        q_values = self.model(states).gather(1, actions).squeeze()
        next_q_values = self.model(next_states).max(1)[0].detach()
        targets = rewards + self.gamma * next_q_values * (1 - dones)
        
        loss = F.mse_loss(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# Define main execution logic
if __name__ == "__main__":
    # Initialize Task Planner & Distributed Executor
    planner = TaskPlanner(strategy="priority")
    executor = DistributedExecutor(mode="hybrid", remote_nodes=[("127.0.0.1", 5000)])

    # Register Agents
    planner.add_agent("Agent1", capacity=3)
    planner.add_agent("Agent2", capacity=2)

    # Define Tasks with Dependencies
    tasks = [
        Task("T1", "Data Collection", priority=5, complexity=2),
        Task("T2", "Data Preprocessing", priority=4, complexity=3, dependencies=["T1"]),
        Task("T3", "Feature Engineering", priority=4, complexity=3, dependencies=["T2"]),
        Task("T4", "Model Training", priority=6, complexity=5, dependencies=["T3"]),
        Task("T5", "Model Evaluation", priority=3, complexity=2, dependencies=["T4"]),
        Task("T6", "Hyperparameter Tuning", priority=7, complexity=5, dependencies=["T4"]),
        Task("T7", "Final Model Deployment", priority=8, complexity=4, dependencies=["T5", "T6"]),
    ]

    # Add Tasks to Planner
    for task in tasks:
        planner.add_task(task)

    # Initialize RL Agent
    state_dim = 2  # Example: task complexity & priority
    action_dim = len(tasks)
    agent = RLAgent(state_dim, action_dim)

    # Task Execution Function
    def execute_task_with_monitoring(agent_id, task):
        """Executes a task with logging and failure handling."""
        print(f"[START] Agent {agent_id} executing task: {task.description}")

        try:
            execution_time = random.uniform(1, 3)  # Simulate execution time
            time.sleep(execution_time)

            if random.random() < 0.1:  # Simulate failure (10% chance)
                raise Exception(f"Simulated failure for task {task.task_id}")

            task.status = "completed"
            print(f"[SUCCESS] Agent {agent_id} completed task: {task.description}")

            # Reward RL Agent for task completion
            state = [task.priority, task.complexity]
            reward = 10  # Positive reward for success
            next_state = state  # Assume static state for now
            agent.store_experience(state, task.task_id, reward, next_state, False)

        except Exception as e:
            print(f"[ERROR] Task {task.task_id} failed: {e}")
            planner.reassign_failed_tasks([task])  # Retry failed tasks
            state = [task.priority, task.complexity]
            reward = -10  # Negative reward for failure
            next_state = state
            agent.store_experience(state, task.task_id, reward, next_state, True)

    # Assign and Execute Tasks
    planner.assign_tasks()
    
    for agent_id, agent_data in planner.agents.items():
        for task in agent_data.assign_task:  # Execute assigned tasks, not completed ones
            execute_task_with_monitoring(agent_id, task)
            executor.execute_task(agent_id, task.description, task_type="light" if task.complexity < 3 else "heavy")
    
    # Train RL Agent
    for _ in range(100):  # Train over multiple iterations
        agent.train()

    # Shutdown after Execution
    planner.shutdown()
    executor.shutdown()
