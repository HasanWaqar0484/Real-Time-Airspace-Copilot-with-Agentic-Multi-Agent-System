# ✈️ Airspace Copilot

An intelligent, agentic AI system for real-time airspace monitoring and flight tracking using multi-agent architecture.

## 🎯 Overview

Airspace Copilot provides two operational modes:
- **Traveler Mode**: Personal flight tracking with natural language Q&A
- **Ops Mode**: Air traffic monitoring with automated anomaly detection

## 🏗️ Architecture

- **n8n**: Workflow orchestration - fetches 8,000+ flights every 60s from OpenSky Network
- **FastAPI MCP Server**: Exposes flight data as tools (list flights, get details, detect anomalies)
- **CrewAI Agents**: Multi-agent reasoning with Groq LLM
  - Ops Analyst: Monitors airspace and identifies issues
  - Traveler Support: Answers flight-related questions
- **Streamlit UI**: Dual-mode interface with live/demo data toggle

## 🚀 Features

✅ Real-time flight data from OpenSky Network API  
✅ Intelligent anomaly detection (low speed, hovering, etc.)  
✅ Natural language query interface  
✅ Region-based flight filtering  
✅ Automated operational summaries  
✅ Live data / Demo data toggle  

## 🛠️ Tech Stack

- **Backend**: Python 3.13, FastAPI, CrewAI
- **LLM**: Groq (llama-3.1-8b-instant)
- **Workflow**: n8n (Docker)
- **Frontend**: Streamlit
- **Data**: OpenSky Network REST API

## 📦 Quick Start

See [README.md](README.md) for detailed setup instructions.

```bash
# 1. Start n8n
docker-compose up -d

# 2. Start MCP Server
uvicorn mcp_server.main:app --reload

# 3. Start Streamlit UI
streamlit run agent_app/app.py
