"""
Multi-Agent Team Framework Demo

This script demonstrates the usage of the multi-agent team framework.
It creates a team of agents with different roles, assigns tasks, and shows
how they collaborate through communication and knowledge sharing.
"""

import sys
import time
from graphfusionai.graph_manager import GraphManager
from graphfusionai.agent import Agent
from graphfusionai.team import Team
from graphfusionai.task import Task
from graphfusionai.logger import FRAMEWORK_LOGGER as logger

# Initialize logger
logger.info(f"Python version: {sys.version}")

if sys.version_info < (3, 9):
    logger.error("Python 3.9 or higher required for type hinting features")
    sys.exit(1)

# Initialize the graph manager
gm = GraphManager()

# Create a team
project_team = Team("ProjectAlpha", gm)

# Define agent capabilities
def plan_task(goal: str) -> dict:
    """Plan how to achieve a goal"""
    logger.info(f"Planning how to achieve: {goal}")
    return {"steps": ["Research", "Design", "Implement", "Test"], "timeline": 14}

def execute_step(step: str) -> str:
    """Execute a development step"""
    logger.info(f"Executing step: {step}")
    time.sleep(1)  # Simulate work
    return f"{step} completed"

def review_work(result: str) -> bool:
    """Review work result"""
    logger.info(f"Reviewing: {result}")
    return "error" not in result.lower()

# Create agents with different roles
planner = Agent("Planner1", "architect", {"plan": plan_task}, gm, project_team)
executor = Agent("Executor1", "developer", {"execute": execute_step}, gm, project_team)
reviewer = Agent("Reviewer1", "qa", {"review": review_work}, gm, project_team)

# Add agents to the team
project_team.add_agent(planner)
project_team.add_agent(executor)
project_team.add_agent(reviewer)

# Create tasks
planning_task = Task("T1", "plan", {"goal": "Build a web service"}).to_dict()
execution_task = Task("T2", "execute", {"step": "Implement API endpoints"}).to_dict()
review_task = Task("T3", "review", {"result": "API implementation"}).to_dict()

# Assign tasks
planner.execute_task(planning_task)
executor.execute_task(execution_task)
reviewer.execute_task(review_task)

# Executor encounters a problem and requests help from Planner
executor.request_help(
    {"type": "plan", "parameters": {"goal": "Design database schema"}},
    "Planner1"
)

# Demonstrate knowledge sharing
planner.contribute_to_knowledge_graph("design_pattern", "Microservices architecture")
retrieved = executor.recall_memory('design_pattern')
logger.info(f"\n[KNOWLEDGE] Executor retrieved design pattern: {retrieved}\n")

# Visualize team structure
logger.info("\nTeam Communication Graph:")
project_team.visualize_communication_graph()

# Save knowledge graph
gm.save_graph()
logger.info("\nDemo completed successfully!")
