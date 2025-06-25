import asyncio
from graphfusionai import Agent, Team, GraphManager

async def main():
    graph_manager = GraphManager()
    
    # Create agents with specific capabilities
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
    
    # Create team and add agents
    project_team = Team(
        team_id="project_alpha",
        graph_manager=graph_manager
    )
    project_team.add_agent(data_analyst)
    project_team.add_agent(research_specialist)
    
    # Define workflow
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
    
    # Start the team and execute workflow
    await project_team.start()
    try:
        results = await project_team.execute_workflow(workflow)
        print("\nWorkflow Results:")
        print(f"Completed: {len(results['completed'])} steps")
        print(f"Failed: {len(results['failed'])} steps")
        
        print("\nDetailed Results:")
        for step_id, result in results['completed'].items():
            print(f"{step_id}: {result}")
            
        for step_id, error in results['failed'].items():
            print(f"{step_id} FAILED: {error}")
            
    finally:
        await project_team.stop()

if __name__ == "__main__":
    asyncio.run(main())
