import asyncio
import logging
from graphfusionai import Agent, Team, GraphManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    team = None
    try:
        logger.info("Initializing Graph Manager")
        graph_manager = GraphManager()
        logger.debug("Graph manager initialized")
        
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
        logger.debug("Agents created")
        
        research_specialist = Agent(
            agent_id="researcher1",
            role="Research Specialist",
            capabilities={
                "find_references": lambda topic: f"References about {topic}",
                "summarize": lambda text: f"Summary: {text[:50]}..."
            },
            graph_manager=graph_manager
        )
        
        loader = Agent(
            agent_id="loader",
            role="Data Loader",
            capabilities={
                "load_data": lambda file: {"content": f"Loaded {file}", "quality": 0.9}
            },
            graph_manager=graph_manager
        )
        
        analyst = Agent(
            agent_id="analyst",
            role="Data Analyst",
            capabilities={
                "analyze_full": lambda data: f"Full analysis of {data}",
                "analyze_basic": lambda data: f"Basic analysis of {data}",
            },
            graph_manager=graph_manager
        )
        
        cleaner = Agent(
            agent_id="cleaner",
            role="Data Cleaner",
            capabilities={
                "clean_data": lambda data: f"Cleaned {data}",
            },
            graph_manager=graph_manager
        )
        
        logger.info("Creating team and adding agents")
        project_team = Team(
            team_id="project_alpha",
            graph_manager=graph_manager,
            state_db=None,
            auto_save_interval=60
        )
        project_team.agents = {
            "analyst1": data_analyst,
            "researcher1": research_specialist,
            "loader": loader,
            "analyst": analyst,
            "cleaner": cleaner
        }
        
        logger.info("Defining workflow")
        workflow = {
            "steps": [
                {
                    "id": "sales_analysis",
                    "agent_id": "analyst1",
                    "task": "analyze_data",
                    "input": {"data": "Q3_sales.csv"},
                    "timeout": 30,
                    "depends_on": []
                },
                {
                    "id": "market_research",
                    "agent_id": "researcher1",
                    "task": "find_references",
                    "input": {"topic": "market_trends"},
                    "timeout": 45,
                    "depends_on": ["sales_analysis"],
                    "retries": 2
                },
                {
                    "id": "report_generation",
                    "agent_id": "analyst1",
                    "task": "generate_report",
                    "input": {"analysis": "{{sales_analysis}}"},
                    "timeout": 30,
                    "depends_on": ["market_research"]
                },
                {
                    "id": "data_load",
                    "agent_id": "loader",
                    "task": "load_data",
                    "input": {"file": "data.csv"},
                    "depends_on": ["report_generation"]
                },
                {
                    "id": "quality_check",
                    "when": "results['data_load']['quality'] > 0.7",
                    "then": [
                        {
                            "id": "full_analysis",
                            "agent_id": "analyst",
                            "task": "analyze_full",
                            "input": {"data": "{{data_load}}"},
                            "depends_on": ["data_load"]
                        }
                    ],
                    "else": [
                        {
                            "id": "cleanup",
                            "agent_id": "cleaner",
                            "task": "clean_data",
                            "input": {"data": "{{data_load}}"},
                            "depends_on": ["data_load"]
                        },
                        {
                            "id": "basic_analysis",
                            "agent_id": "analyst",
                            "task": "analyze_basic",
                            "input": {"data": "{{cleanup}}"},
                            "depends_on": ["cleanup"]
                        }
                    ]
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
                print(f"{step_id}: {result}")
                
            for step_id, error in results['failed'].items():
                print(f"{step_id} FAILED: {error}")
                
        except asyncio.CancelledError:
            logger.error("Workflow execution was cancelled")
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
        finally:
            logger.info("Stopping team")
            await project_team.stop()

    except asyncio.CancelledError:
        logger.error("Workflow execution was cancelled")
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
    finally:
        if team:
            await team.stop()

if __name__ == "__main__":
    asyncio.run(main())
