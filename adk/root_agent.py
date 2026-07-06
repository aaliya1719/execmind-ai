from google.adk.agents import Agent
from app.agents.manager_agent import build_report


root_agent = Agent(
    name="execmind_manager",
    model="gemini-2.5-flash",
    description="Executive AI business consultant that coordinates multiple business agents.",
    instruction="""
You are the Manager Agent of ExecMind AI.

Your responsibility is to coordinate business analysis using the available tools and provide a single executive business report.

Always produce structured, business-friendly recommendations.
""",
    tools=[build_report],
)