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
                "id": "data_prep",
                "agent_id": "analyst1",
                "task": "analyze_data",
                "input": {"data": "raw_dataset.csv"},
                "depends_on": []
            },
            # Parallel processing steps
            {
                "id": "feature_eng",
                "agent_id": "analyst1",
                "task": "analyze_data",
                "parallel": True,
                "input": {"data": "{{data_prep}}"},
                "depends_on": ["data_prep"]
            },
            {
                "id": "stats_analysis",
                "agent_id": "analyst1",
                "task": "analyze_data",
                "parallel": True,
                "input": {"data": "{{data_prep}}"},
                "depends_on": ["data_prep"]
            },
            # Final serial step
            {
                "id": "report_gen",
                "agent_id": "analyst1",
                "task": "generate_report",
                "input": {
                    "analysis": "{{feature_eng}}",
                    "stats": "{{stats_analysis}}"
                },
                "depends_on": ["feature_eng", "stats_analysis"]
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
