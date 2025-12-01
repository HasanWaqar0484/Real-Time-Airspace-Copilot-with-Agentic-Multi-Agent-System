# Airspace Copilot - Agentic AI System

A real-time flight monitoring system using n8n, MCP, CrewAI, and Groq LLM.

## Architecture

- **n8n**: Fetches flight data from OpenSky Network API every 60 seconds
- **MCP Server**: FastAPI server exposing flight data tools
- **Agentic Layer**: CrewAI agents (Ops Analyst & Traveler Support)
- **UI**: Streamlit app with Traveler and Ops modes

## Prerequisites

- Docker Desktop (running)
- Python 3.13
- Groq API Key

## Setup Instructions

### 1. Environment Setup

The `.env` file is already configured with your Groq API key.

### 2. Start n8n

n8n is already running on port 5678. If not:

```bash
docker-compose up -d
```

Access n8n at `http://localhost:5678`

### 3. Import n8n Workflow

1. Open `http://localhost:5678`
2. Skip setup if prompted
3. Go to **Workflows** → **Import from File**
4. Select `n8n_workflow.json`
5. **Activate** the workflow (toggle in top right)
6. Click **Execute Workflow** to fetch initial data

### 4. Install Python Dependencies

```bash
pip install -r mcp_server/requirements.txt
pip install -r agent_app/requirements.txt
```

### 5. Run the MCP Server

In one terminal:

```bash
uvicorn mcp_server.main:app --reload
```

Server runs on `http://localhost:8000`

### 6. Run the Streamlit App

In another terminal:

```bash
streamlit run agent_app/app.py
```

App opens at `http://localhost:8501`

## Usage

### Traveler Mode

1. Enter a flight callsign (e.g., `THY4KZ`) or ICAO24 ID
2. Ask questions like:
   - "Where is my flight now?"
   - "Is my flight climbing or descending?"
   - "What is the current altitude?"

### Ops Mode

1. Select a region (Region A or Region B)
2. Click **Refresh Region Status**
3. View:
   - Flight table with anomaly flags
   - AI-generated operational summary

## Components

### MCP Server (`mcp_server/main.py`)

Exposes three tools:
- `GET /flights/list?region=<name>` - List flights in a region
- `GET /flights/get?callsign=<id>` - Get specific flight details
- `GET /alerts/list` - List anomalies

### Agents (`agent_app/agents.py`)

- **Ops Analyst Agent**: Monitors airspace, identifies anomalies
- **Traveler Support Agent**: Answers user questions about flights

### n8n Workflow

1. **Schedule Trigger**: Runs every 60 seconds
2. **Fetch OpenSky Data**: Calls OpenSky API
3. **Format Data**: Converts to JSON
4. **Send to MCP Server**: POSTs data to `/update-flights` endpoint

The MCP server receives the data and saves it to `data/flights.json`.

## Data Flow

```
OpenSky API → n8n → data/flights.json → MCP Server → CrewAI Agents → Streamlit UI
```

## Troubleshooting

### Port 5678 already in use
n8n is already running. Check with `docker ps`.

### MCP Server not responding
Ensure `uvicorn mcp_server.main:app --reload` is running.

### No flight data
1. Check n8n workflow is activated
2. Execute workflow manually once
3. Verify `data/flights.json` exists and has data

### API Rate Limits
OpenSky API has rate limits. The system uses cached data from `flights.json` when API is unavailable.

## Sample Data

Sample data is pre-populated in `data/flights.json` for testing.

## Notes

- The system works with cached data if OpenSky API is unavailable
- Anomaly detection uses simple thresholds (configurable in `mcp_server/main.py`)
- A2A communication is enabled between agents (Traveler Support can delegate to Ops Analyst)
