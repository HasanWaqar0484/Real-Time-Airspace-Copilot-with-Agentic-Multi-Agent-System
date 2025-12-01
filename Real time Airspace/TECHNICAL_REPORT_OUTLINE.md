# Airspace Copilot - Technical Report

## 1. Introduction & Problem Statement

### 1.1 Background
Air traffic monitoring is critical for aviation safety and operational efficiency. Traditional systems often lack:
- Real-time anomaly detection
- Natural language interfaces for non-technical users
- Intelligent analysis of flight patterns
- Accessible information for travelers

### 1.2 Problem Statement
There is a need for an intelligent, agentic system that can:
1. Monitor live airspace in real-time
2. Detect and explain anomalies automatically
3. Provide natural language interfaces for both operations teams and travelers
4. Integrate multiple data sources and tools seamlessly

### 1.3 Solution: Airspace Copilot
An agentic AI system that combines:
- **n8n** for workflow orchestration and data fetching
- **MCP (Model Context Protocol)** for tool exposure
- **CrewAI** for multi-agent reasoning
- **Groq LLM** for natural language understanding
- **Streamlit** for user interface

### 1.4 Gap Filled
This system bridges the gap between raw flight data and actionable insights by providing:
- Automated anomaly detection with explanations
- Conversational interfaces for flight information
- Real-time monitoring with intelligent alerts
- Dual-mode operation for different user personas

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Airspace Copilot System                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   OpenSky    │      │              │      │              │
│   Network    │─────▶│     n8n      │─────▶│   flights    │
│     API      │      │   Workflow   │      │   .json      │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                    │
                      ┌─────────────────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │  MCP Server  │
              │   (FastAPI)  │
              └──────┬───────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  /flights/list  /flights/get  /alerts/list
        │            │            │
        └────────────┼────────────┘
                     │
              ┌──────▼───────┐
              │   CrewAI     │
              │   Agents     │
              ├──────────────┤
              │ Ops Analyst  │
              │   Traveler   │
              │   Support    │
              └──────┬───────┘
                     │
              ┌──────▼───────┐
              │  Streamlit   │
              │      UI      │
              ├──────────────┤
              │ Traveler Mode│
              │   Ops Mode   │
              └──────────────┘
```

### 2.1 Data Flow
1. **n8n** fetches flight data from OpenSky API every 60 seconds
2. Data is formatted and saved to shared `flights.json` file
3. **MCP Server** reads the file and exposes three tool endpoints
4. **CrewAI Agents** call MCP tools to fetch data
5. **Groq LLM** processes data and generates natural language responses
6. **Streamlit UI** displays results to users

---

## 3. n8n Workflow

### 3.1 Workflow Design
The n8n workflow consists of 4 nodes:

1. **Schedule Trigger**
   - Executes every 60 seconds
   - Ensures continuous data refresh

2. **Fetch OpenSky Data**
   - HTTP Request to `https://opensky-network.org/api/states/all`
   - Retrieves global flight state vectors
   - Returns 8,000+ flights in real-time

3. **Format Data**
   - JavaScript Code node
   - Transforms OpenSky array format to structured JSON
   - Maps 17 flight parameters (icao24, callsign, position, velocity, etc.)

4. **Send to MCP Server**
   - HTTP POST to `http://host.docker.internal:8000/update-flights`
   - Saves formatted data for MCP server consumption

### 3.2 Data Storage
- **Location**: `data/flights.json`
- **Format**: JSON array of flight objects
- **Update Frequency**: Every 60 seconds
- **Shared Access**: Both n8n and MCP server access this file
- **Typical Size**: 8,000+ flights (~2MB)

### 3.3 Snapshot Structure
```json
[
  {
    "icao24": "a4d86a",
    "callsign": "LXJ411",
    "origin_country": "United States",
    "longitude": -85.4336,
    "latitude": 32.614,
    "baro_altitude": 175.26,
    "velocity": 0,
    "true_track": 272.81,
    ...
  }
]
```

---

## 4. MCP Server & Tools

### 4.1 Technology Stack
- **Framework**: FastAPI
- **Language**: Python 3.13
- **Port**: 8000
- **Protocol**: HTTP REST API

### 4.2 Tool Endpoints

#### 4.2.1 `/flights/list` - List Flights in Region
**Purpose**: Retrieve flights filtered by geographic region

**Parameters**:
- `region` (optional): "Region A" or "Region B"
- `limit` (default: 2): Maximum flights to return

**Logic**:
- Hardcoded region boundaries (lat/lon bounding boxes)
- Region A: Europe (40-50°N, -10-10°E)
- Region B: USA (25-45°N, -125--70°W)
- Returns filtered list based on flight coordinates

**Response**: JSON array of flight objects

#### 4.2.2 `/flights/get` - Get Flight Details
**Purpose**: Retrieve specific flight by identifier

**Parameters**:
- `callsign`: Flight callsign or ICAO24 ID

**Logic**:
- Searches by callsign (case-insensitive)
- Falls back to ICAO24 search
- Returns 404 if not found

**Response**: Single flight object or error

#### 4.2.3 `/alerts/list` - List Active Alerts
**Purpose**: Detect and return flight anomalies

**Parameters**:
- `limit` (default: 1): Maximum alerts to return

**Anomaly Detection Logic**:
1. **Low Speed at High Altitude**
   - Altitude > 10,000m AND velocity < 100 m/s
   - Severity: HIGH
   
2. **Stationary/Hovering**
   - Not on ground AND velocity < 10 m/s
   - Severity: MEDIUM

**Response**: JSON array of anomaly objects with descriptions

### 4.3 Data Flow Optimization
To work within Groq API rate limits:
- Flight list limited to 2 flights (configurable)
- Alerts limited to 1 alert (configurable)
- Reduces token usage from ~5,000 to ~2,000 per query

---

## 5. Agents, Prompts & A2A Communication

### 5.1 Agent Architecture
Built using **CrewAI** framework with **Groq LLM** (llama-3.1-8b-instant)

#### 5.1.1 Ops Analyst Agent
**Role**: Monitor airspace and identify anomalies

**Tools**:
- `List Flights in Region`
- `List Active Alerts`
- `Get Flight Details`

**Capabilities**:
- Analyzes flight patterns in specific regions
- Identifies anomalies using rule-based detection
- Provides operational summaries

**Optimizations**:
- `max_iter=2`: Limits reasoning iterations
- `memory=False`: Disables conversation history
- `verbose=False`: Reduces output tokens

#### 5.1.2 Traveler Support Agent
**Role**: Answer traveler questions about flights

**Tools**:
- `Get Flight Details`

**Capabilities**:
- Fetches specific flight information
- Explains flight status in natural language
- Handles "flight not found" scenarios gracefully

**Optimizations**:
- Shorter prompts ("Agent." vs long backstories)
- `max_iter=2`
- `memory=False`

### 5.2 Prompt Engineering
**Before Optimization**:
```python
backstory='You are an experienced air traffic operations analyst. 
You monitor flight data for safety and efficiency.'
```

**After Optimization**:
```python
backstory='Analyst.'
```

**Token Reduction**: ~60% reduction in system prompt tokens

### 5.3 A2A (Agent-to-Agent) Communication
**Implementation**:
- Both agents included in same Crew
- `allow_delegation=False` (disabled for token optimization)
- Originally enabled for complex queries requiring multiple perspectives

**Use Case** (when enabled):
- Traveler Support can delegate complex questions to Ops Analyst
- Example: "Are there any issues affecting flights in my region?"

**Current Status**: Disabled to minimize token usage for Groq free tier

---

## 6. UI Design & User Journey

### 6.1 Technology
- **Framework**: Streamlit
- **Port**: 8501
- **Layout**: Wide mode with sidebar

### 6.2 UI Components

#### 6.2.1 Sidebar Configuration
**Data Source Toggle**:
- "Live Data (OpenSky)": Real-time data from n8n
- "Demo Data (Cached)": Stable sample data for testing

**Region Selector**:
- Region A (Europe)
- Region B (USA)

#### 6.2.2 Traveler Mode Tab
**Purpose**: Personal flight tracking for travelers

**User Journey**:
1. Enter flight callsign (e.g., "LXJ411")
2. Type question (e.g., "Where is my flight now?")
3. Click "Ask Agent"
4. View natural language response with flight details

**Example Output**:
```
Your flight LXJ411 is currently at coordinates 
-85.43°W, 32.61°N (over Alabama, USA) at an 
altitude of 175 meters, traveling at 0 m/s.
```

#### 6.2.3 Ops Mode Tab
**Purpose**: Operational monitoring for air traffic controllers

**User Journey**:
1. Select region from sidebar
2. Click "Refresh Region Status"
3. View:
   - AI-generated operational summary
   - Flight data table with anomaly flags
   - Alert descriptions

**Example Output**:
```
Operational Summary:
Region B has 2 active flights. 1 anomaly detected:
- LXJ411: Stationary/Hovering in air (0 m/s) - MEDIUM severity
```

### 6.3 Screenshots
*(Include screenshots of:)*
1. Sidebar with data source toggle
2. Traveler Mode query and response
3. Ops Mode with flight table and summary
4. n8n workflow canvas

---

## 7. Limitations & Future Improvements

### 7.1 Current Limitations

#### 7.1.1 API Rate Limits
**Issue**: Groq free tier limits (6,000 tokens/min)
- Even with optimizations, only 2-3 queries/minute possible
- Limits real-time responsiveness

**Mitigation**:
- Data source toggle for demo vs live data
- Reduced data limits (2 flights, 1 alert)
- Optimized prompts and disabled memory

**Future**: Upgrade to Groq paid tier or implement request queuing

#### 7.1.2 Anomaly Detection
**Issue**: Simple rule-based detection
- Only 2 anomaly types implemented
- No historical pattern analysis
- No machine learning

**Future**: 
- ML-based anomaly detection
- Historical trend analysis
- Predictive alerts

#### 7.1.3 Region Definitions
**Issue**: Hardcoded region boundaries
- Only 2 regions supported
- Fixed geographic boundaries

**Future**:
- Dynamic region creation
- User-defined areas of interest
- Polygon-based region selection

#### 7.1.4 Scalability
**Issue**: File-based data storage
- Single JSON file for all flights
- No database indexing
- Limited query performance

**Future**:
- Database backend (PostgreSQL/MongoDB)
- Caching layer (Redis)
- Horizontal scaling

### 7.2 Future Improvements

#### 7.2.1 Enhanced Features
1. **Map Visualization**
   - Interactive flight map
   - Real-time position updates
   - Flight path history

2. **Advanced Analytics**
   - Flight delay predictions
   - Congestion analysis
   - Weather integration

3. **Notifications**
   - Email/SMS alerts for anomalies
   - Webhook integrations
   - Custom alert rules

4. **Multi-User Support**
   - User authentication
   - Saved preferences
   - Watchlists

#### 7.2.2 Technical Improvements
1. **Performance**
   - Database indexing
   - Response caching
   - Async processing

2. **Reliability**
   - Error handling and retries
   - Fallback data sources
   - Health monitoring

3. **Security**
   - API authentication
   - Rate limiting per user
   - Data encryption

---

## 8. Conclusion

The Airspace Copilot system successfully demonstrates:
- ✅ Real-time data integration (8,000+ flights)
- ✅ Intelligent anomaly detection
- ✅ Natural language interfaces
- ✅ Multi-agent reasoning with MCP
- ✅ Dual-mode operation for different users

Despite rate limit constraints, the system provides a solid foundation for production deployment with proper infrastructure and paid API tiers.

---

## Appendix A: Technology Stack Summary

| Component | Technology | Version |
|-----------|-----------|---------|
| Workflow Engine | n8n | Latest (Docker) |
| MCP Server | FastAPI | 0.104+ |
| Agent Framework | CrewAI | Latest |
| LLM Provider | Groq | llama-3.1-8b-instant |
| UI Framework | Streamlit | Latest |
| Data Source | OpenSky Network | REST API |
| Language | Python | 3.13 |
| Container | Docker | Latest |

## Appendix B: File Structure

```
assignment4/
├── .env                    # API keys
├── docker-compose.yml      # n8n container config
├── n8n_workflow.json      # Workflow export
├── data/
│   ├── flights.json       # Live data
│   └── flights_demo.json  # Demo data
├── mcp_server/
│   ├── main.py           # FastAPI server
│   └── requirements.txt
└── agent_app/
    ├── app.py            # Streamlit UI
    ├── agents.py         # CrewAI agents
    └── requirements.txt
```

## Appendix C: API Endpoints Reference

### MCP Server (Port 8000)
- `GET /flights/list?region={name}&limit={n}`
- `GET /flights/get?callsign={id}`
- `GET /alerts/list?limit={n}`
- `POST /update-flights` (from n8n)

### n8n (Port 5678)
- Web UI: `http://localhost:5678`
- Workflow execution: Manual or scheduled

### Streamlit (Port 8501)
- Web UI: `http://localhost:8501`
