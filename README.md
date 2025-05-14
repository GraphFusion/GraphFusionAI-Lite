# GraphFusionAI-Lite

GraphFusionAI-Lite is a lightweight,experimental graph-based multi-agent system designed to enable autonomous AI agents to collaborate effectively on complex tasks. It provides a structured yet dynamic approach to multi-agent coordination, leveraging graphs for communication, task execution, and knowledge sharing.

## Features

✅ **Graph-Based Architecture** – Uses NetworkX to model agent interactions and task dependencies.
✅ **Multi-Agent System** – Agents collaborate dynamically based on predefined roles.
✅ **Hybrid Execution** – Supports both multi-threading (for speed) and multi-processing (for heavy tasks).
✅ **Task Planning & Execution** – Uses a TaskPlanner and DistributedExecutor for optimized scheduling.
✅ **Reinforcement Learning (RL) & LLMs** – Enables adaptive, intelligent agents that improve over time.
✅ **Fault Tolerance & Self-Healing** – Includes mechanisms for agent recovery and retry logic.
✅ **Lightweight Storage** – Uses SQLite for knowledge graph persistence and efficient querying.

## Installation

### Prerequisites
- Python 3.8+
- `pip` package manager

### Install via pip
```sh
pip install graphfusionai-lite
```

### Install from source
```sh
git clone https://github.com/your-repo/GraphFusionAI-Lite.git
cd GraphFusionAI-Lite
pip install -r requirements.txt
```
## Getting Started

### Import the Library
```python
from graphfusionai.core import Agent, Task
from graphfusionai.planning import TaskPlanner
from graphfusionai.distributed import DistributedExecutor
```

### Initialize Task Planner & Executor
```python
planner = TaskPlanner(strategy="priority")
executor = DistributedExecutor(mode="hybrid", remote_nodes=[("127.0.0.1", 5000)])
```

### Define Agents
```python
planner.add_agent("Agent1", capacity=3)
planner.add_agent("Agent2", capacity=2)
```

### Define & Add Tasks
```python
tasks = [
    Task("T1", "Data Collection", priority=5, complexity=2),
    Task("T2", "Data Preprocessing", priority=4, complexity=3, dependencies=["T1"]),
    Task("T3", "Feature Engineering", priority=4, complexity=3, dependencies=["T2"]),
]

for task in tasks:
    planner.add_task(task)
```

### Assign & Execute Tasks
```python
planner.assign_tasks()
executor.execute_all(planner.agents)
```

### Shutdown After Execution
```python
planner.shutdown()
executor.shutdown()
```

## Architecture Overview

GraphFusionAI-Lite operates using a hybrid graph-based model:
1. **Agent Graph** – Defines relationships between AI agents.
2. **Task Graph** – Manages dependencies and execution flow.
3. **Execution Engine** – Assigns tasks to agents and executes them in an optimized manner.
4. **Reinforcement Learning (Upcoming)** – Uses RL algorithms (DQN, PPO) to enhance agent learning.

## Roadmap
🚀 **Integrate Reinforcement Learning (DQN, PPO) for Adaptive Agents**
⚡ **Enhance Distributed Execution Across Machines**
📊 **Improve Graph Database Storage & Querying**

## Contributing

We welcome contributions! Feel free to submit issues and pull requests.

### Steps to Contribute
1. Fork the repository
2. Clone your fork
   ```sh
   git clone https://github.com/your-username/GraphFusionAI-Lite.git
   ```
3. Create a new branch
   ```sh
   git checkout -b feature-name
   ```
4. Make changes and commit
   ```sh
   git commit -m "Add new feature"
   ```
5. Push to your fork and create a pull request

## License
GraphFusionAI-Lite is licensed under the MIT License. See `LICENSE` for details.


## Contact
For questions or suggestions, open an issue or reach out via korirkiplangat22@gmail.com.

