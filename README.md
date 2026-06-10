---
title: TracePilot
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# TracePilot

> **Note for Judges (Hosted Project):** Local-first architecture to protect enterprise data—requires local execution to view the Arize Phoenix telemetry dashboard. Please follow the instructions below to run locally.

TracePilot is an autonomous FinOps routing agent that learns from operational observability data. Built for the Arize AI track of the Google Cloud Rapid Agent Hackathon.

## Features
- **Economic Memory Engine**: Learns which tools and routes perform best based on cost, latency, and success rates.
- **Phoenix MCP Auditor**: Continuously audits telemetry data via the Phoenix SDK to discover inefficiencies and update routing confidence.
- **Mock Google Auth**: Realistic demo-ready UI.

## Getting Started

1. Set up a Python 3.10+ virtual environment:
   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the Arize Phoenix telemetry server in the background:
   ```bash
   python -m phoenix.server.main serve
   ```
   *(The server will run at http://localhost:6006)*

3. Run the TracePilot demo server:
   ```bash
   uvicorn tracepilot.api:app --host 0.0.0.0 --port 5000 --reload
   ```

4. Open `http://localhost:5000` in your browser.
