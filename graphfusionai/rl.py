import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random

class GraphFusionEnv(gym.Env):
    """
    Custom RL environment for task execution optimization in GraphFusionAI.
    """
    def __init__(self, num_tasks=5, max_steps=20):
        super(GraphFusionEnv, self).__init__()
        
        self.num_tasks = num_tasks
        self.max_steps = max_steps
        self.current_step = 0
        
        # Define action & observation space
        self.action_space = spaces.Discrete(num_tasks)  # Choose which task to execute
        self.observation_space = spaces.Box(low=0, high=1, shape=(num_tasks,), dtype=np.float32)
        
        # Task state: [0] - pending, [1] - completed
        self.task_state = np.zeros(num_tasks, dtype=np.float32)
        
        # Task execution cost (randomized for simulation)
        self.task_costs = np.random.randint(1, 5, size=num_tasks)

    def reset(self, seed=None, options=None):
        """Resets the environment for a new episode."""
        super().reset(seed=seed)
        self.current_step = 0
        self.task_state = np.zeros(self.num_tasks, dtype=np.float32)
        self.task_costs = np.random.randint(1, 5, size=self.num_tasks)
        return self.task_state, {}

    def step(self, action):
        """Executes a task and updates state."""
        self.current_step += 1
        
        if self.task_state[action] == 1:  # Task already completed
            reward = -1  # Penalty for redundant execution
        else:
            execution_time = self.task_costs[action]
            reward = 10 / execution_time  # Reward inversely proportional to cost
            self.task_state[action] = 1  # Mark task as completed
        
        done = all(self.task_state) or self.current_step >= self.max_steps
        return self.task_state, reward, done, False, {}

    def render(self):
        """Renders the current environment state."""
        print(f"Step: {self.current_step}, Task State: {self.task_state}")

# Test Environment
if __name__ == "__main__":
    env = GraphFusionEnv(num_tasks=5)
    obs, _ = env.reset()
    done = False
    while not done:
        action = env.action_space.sample()  
        obs, reward, done, _, _ = env.step(action)
        env.render()
    print("Simulation Complete!")
