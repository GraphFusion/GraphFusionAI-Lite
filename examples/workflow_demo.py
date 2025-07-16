import asyncio
import logging
from graphfusionai import Agent, Team, GraphManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing Graph Manager")
    graph_manager = GraphManager()
    
    logger.info("Creating agents")
    data_analyst = Agent(
        agent_id="analyst1",
        role="Data Analyst",
        capabilities={
            "analyze_data": lambda data: f"Analysis of {data}",
            "generate_report": lambda analysis: f"Report: {analysis}"
        },
        graph_manager=graph_manager
    )
    
    research_specialist = Agent(
        agent_id="researcher1",
        role="Research Specialist",
        capabilities={
            "find_references": lambda topic: f"References about {topic}",
            "summarize": lambda text: f"Summary: {text[:50]}..."
        },
        graph_manager=graph_manager
    )
    
    logger.info("Creating team and adding agents")
    project_team = Team(
        team_id="project_alpha",
        graph_manager=graph_manager
    )
    await project_team.add_agent(data_analyst)
    await project_team.add_agent(research_specialist)
    
    logger.info("Defining workflow")
    workflow = {
        "steps": [
            {
                "id": "sales_analysis",
                "agent_id": "analyst1",
                "task": "analyze_data",
                "input": {"data": "Q3_sales.csv"},
                "depends_on": []
            },
            {
                "id": "market_research",
                "agent_id": "researcher1",
                "task": "find_references",
                "input": {"topic": "market_trends"},
                "depends_on": ["sales_analysis"],
                "retries": 2
            },
            {
                "id": "report_generation",
                "agent_id": "analyst1",
                "task": "generate_report",
                "input": {"analysis": "{{sales_analysis}}"},
                "depends_on": ["market_research"]
            }
        ]
    }
    
    logger.info("Starting team")
    await project_team.start()
    try:
        logger.info("Executing workflow")
        results = await project_team.execute_workflow(workflow)
        logger.info("Workflow execution completed")
        print("\nWorkflow Results:")
        print(f"Completed: {len(results['completed'])} steps")
        print(f"Failed: {len(results['failed'])} steps")
        
        print("\nDetailed Results:")
        for step_id, result in results['completed'].items():
            logger.info(f"Step {step_id} completed with result: {result}")
            print(f"{step_id}: {result}")
            
        for step_id, error in results['failed'].items():
            logger.error(f"Step {step_id} failed with error: {error}")
            print(f"{step_id} FAILED: {error}")
            
    finally:
        logger.info("Stopping team")
        await project_team.stop()

if __name__ == "__main__":
    asyncio.run(main())
