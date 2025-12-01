import streamlit as st
import agents
import pandas as pd
import requests

st.set_page_config(page_title="Airspace Copilot", layout="wide")

st.title("✈️ Airspace Copilot Agentic System")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Data source toggle
data_source = st.sidebar.radio(
    "Data Source",
    ["Live Data (OpenSky)", "Demo Data (Cached)"],
    help="Live data may hit rate limits. Demo data is stable for testing."
)

# Set environment variable for agents to use
import os
os.environ["USE_DEMO_DATA"] = "true" if "Demo" in data_source else "false"

region = st.sidebar.selectbox("Select Region", ["Region A", "Region B"])

# Tabs
tab1, tab2 = st.tabs(["Traveler Mode", "Ops Mode"])

with tab1:
    st.header("Personal Flight Watchdog")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        flight_id = st.text_input("Enter Flight Callsign or ICAO24", value="THY4KZ")
        user_query = st.text_area("Ask a question about your flight", value="Where is my flight now?")
        ask_btn = st.button("Ask Agent")
    
    with col2:
        if ask_btn and flight_id and user_query:
            with st.spinner("Agent is thinking..."):
                try:
                    response = agents.run_traveler_query(user_query, flight_id)
                    st.success("Response:")
                    st.markdown(response)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.header("Airspace Ops Copilot")
    
    if st.button("Refresh Region Status"):
        with st.spinner("Analyzing airspace..."):
            try:
                # 1. Get raw data for table
                # We can call the MCP tool directly or via agent, but for the table we might want raw data.
                # Let's use the agent for the summary and raw request for the table.
                flights_data = requests.get(f"http://localhost:8000/flights/list?region={region}").json()
                alerts_data = requests.get("http://localhost:8000/alerts/list").json()
                
                # Display Summary
                summary = agents.run_ops_analysis(region)
                st.info("Operational Summary")
                st.markdown(summary)
                
                # Display Flights Table
                st.subheader("Live Flight Data")
                if flights_data:
                    df = pd.DataFrame(flights_data)
                    # Add anomaly flag
                    anomalies = {a['icao24']: a['description'] for a in alerts_data}
                    df['Anomaly'] = df['icao24'].map(anomalies).fillna("Normal")
                    
                    # Select columns
                    cols = ['callsign', 'icao24', 'baro_altitude', 'velocity', 'on_ground', 'Anomaly']
                    # Filter cols that exist
                    cols = [c for c in cols if c in df.columns]
                    st.dataframe(df[cols])
                else:
                    st.warning("No flights found in this region.")
                    
            except Exception as e:
                st.error(f"Error: {e}")

