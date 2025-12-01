import os
import requests
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

MCP_URL = "http://localhost:8000"

from crewai.tools import tool

class FlightTools:
    @tool("List Flights in Region")
    def list_flights(region: str):
        """Get flights in region."""
        try:
            response = requests.get(f"{MCP_URL}/flights/list", params={"region": region})
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error: {e}"

    @tool("Get Flight Details")
    def get_flight(callsign: str):
        """Get flight by callsign."""
        try:
            response = requests.get(f"{MCP_URL}/flights/get", params={"callsign": callsign})
            if response.status_code == 404:
                return "Flight not found."
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error: {e}"

    @tool("List Active Alerts")
    def list_alerts():
        """Get alerts."""
        try:
            response = requests.get(f"{MCP_URL}/alerts/list")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error: {e}"

# LLM
llm_model = "groq/llama-3.1-8b-instant"

# Agents - optimized for minimal tokens
ops_analyst = Agent(
    role='Ops Analyst',
    goal='Monitor airspace',
    backstory='Analyst.',
    tools=[FlightTools.list_flights, FlightTools.list_alerts],
    verbose=False,
    llm=llm_model,
    allow_delegation=False,
    max_iter=2,
    memory=False
)

traveler_support = Agent(
    role='Support',
    goal='Answer questions',
    backstory='Agent.',
    tools=[FlightTools.get_flight],
    verbose=False,
    llm=llm_model,
    allow_delegation=False,
    max_iter=2,
    memory=False
)

def run_ops_analysis(region: str):
    task = Task(
        description=f"List flights in {region} and alerts. Summarize.",
        expected_output="Brief summary.",
        agent=ops_analyst
    )
    crew = Crew(
        agents=[ops_analyst],
        tasks=[task],
        process=Process.sequential,
        memory=False,
        verbose=False
    )
    result = crew.kickoff()
    return str(result.raw) if hasattr(result, 'raw') else str(result)

def run_traveler_query(user_query: str, callsign: str):
    task = Task(
        description=f"Get flight {callsign}. Answer: '{user_query}'",
        expected_output="Brief answer.",
        agent=traveler_support
    )
    crew = Crew(
        agents=[traveler_support],
        tasks=[task],
        process=Process.sequential,
        memory=False,
        verbose=False
    )
    result = crew.kickoff()
    return str(result.raw) if hasattr(result, 'raw') else str(result)
