"""
Multi-Agent Team Framework Demo

This script demonstrates the usage of the multi-agent team framework.
It creates a team of agents with different roles, assigns tasks, and shows
how they collaborate through communication and knowledge sharing.
"""

import sys
import time
import asyncio
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

# Define agent capabilities
async def plan_task(goal: str) -> dict:
    """Plan how to achieve a goal"""
    logger.info(f"Planning how to achieve: {goal}")
    return {"steps": ["Research", "Design", "Implement", "Test"], "timeline": 14}

async def execute_step(step: str) -> str:
    """Execute a development step"""
    logger.info(f"Executing step: {step}")
    await asyncio.sleep(1)  # Simulate work
    return f"{step} completed"

async def review_work(result: str) -> bool:
    """Review work result"""
    logger.info(f"Reviewing: {result}")
    return "error" not in result.lower()

async def main():
    # Initialize the graph manager
    gm = GraphManager()
    
    # Create team
    project_team = Team("ProjectAlpha", gm)
    
    # Create agents
    planner = Agent("Planner1", "planner", {"plan": plan_task}, gm)
    executor = Agent("Executor1", "executor", {"execute": execute_step}, gm)
    reviewer = Agent("Reviewer1", "reviewer", {"review": review_work}, gm)
    
    agents = [planner, executor, reviewer]
    
    # Add agents to team
    for agent in agents:
        await project_team.add_agent(agent)

    # Start agents and team
    for agent in agents:
        await agent.start()
    await project_team.start()

    try:
        # Assign tasks
        plan = await planner.execute_task({"type": "plan", "parameters": {"goal": "Build a web service"}})
        
        # Execute steps
        for step in plan["steps"]:
            result = await executor.execute_task({"type": "execute", "parameters": {"step": step}})
            review_result = await reviewer.execute_task({"type": "review", "parameters": {"result": result}})
            if not review_result:
                logger.error(f"Review failed for step: {step}")
                
        # Request help
        await executor.request_help(
            {"type": "plan", "parameters": {"goal": "Design database schema"}},
            "Planner1"
        )
        
        # Demonstrate knowledge sharing
        await planner.contribute_to_knowledge_graph("design_pattern", "Microservices architecture")
        retrieved = await executor.recall_memory('design_pattern')
        logger.info(f"\n[KNOWLEDGE] Executor retrieved design pattern: {retrieved}\n")
        
        # Visualize team structure
        logger.info("\nTeam Communication Graph:")
        project_team.visualize_communication_graph()
        
        # Save knowledge graph
        gm.save_graph()
        logger.info("\nDemo completed successfully!")

    finally:
        # Stop agents and team
        for agent in agents:
            await agent.stop()
        await project_team.stop()

if __name__ == "__main__":
    asyncio.run(main())
