# GraphFusionAI-Lite: A Scalable Multi-Agent Collaboration Framework

GraphFusionAI-Lite is a Python framework for building collaborative multi-agent systems using asynchronous programming and knowledge graphs. It enables AI agents to work together on complex tasks by providing structured communication, task delegation, and shared knowledge management.

## Why GraphFusionAI-Lite?

Modern AI systems often require multiple specialized agents working together. Traditional approaches face challenges with:
- Coordination overhead
- Knowledge siloing
- Scalability limitations
- Concurrency bottlenecks

GraphFusionAI-Lite solves these by providing:
1. **Asynchronous Agent Communication**: Using Python's asyncio for efficient concurrency
2. **Centralized Knowledge Graph**: Enabling agents to share and query information
3. **Team-based Collaboration**: Agents can form dynamic teams for task delegation
4. **Extensible Architecture**: Easy to add new agent capabilities and behaviors

## Core Concepts

### Agents
Agents are autonomous entities that can:
- Execute tasks using capabilities (async or sync)
- Communicate with other agents
- Store and recall information
- Request and provide help

### Teams
Teams coordinate agents by:
- Managing agent membership
- Routing messages between agents
- Tracking task completion
- Maintaining a communication graph

### Knowledge Graph
The graph stores:
- Agent nodes with attributes
- Knowledge nodes (facts, data, insights)
- Communication events
- Relationships between entities

### Asynchronous Architecture
All agent inter