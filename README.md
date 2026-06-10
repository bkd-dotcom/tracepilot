---
title: TracePilot
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

<p align="center">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="100%">
    <defs>
      <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#0f2027;stop-opacity:1" />
        <stop offset="50%" style="stop-color:#203a43;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#2c5364;stop-opacity:1" />
      </linearGradient>
      <linearGradient id="text-grad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:#00c6ff;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#0072ff;stop-opacity:1" />
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" rx="20" fill="url(#bg-grad)"/>
    <text x="50%" y="45%" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="72" font-weight="900" fill="url(#text-grad)" text-anchor="middle" dominant-baseline="middle" letter-spacing="2">TracePilot</text>
    <text x="50%" y="75%" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="22" font-weight="400" fill="#e0e0e0" text-anchor="middle" dominant-baseline="middle" letter-spacing="1">Self-Healing Agents through Observability</text>
  </svg>
</p>

TracePilot is an autonomous enterprise routing agent that **learns from its own observability traces** rather than relying on hardcoded LLM prompts. Built using the Google Agent Development Kit (ADK) and Arize Phoenix for the Google Cloud Rapid Agent Hackathon.

## The Core Concept: Why Not Just Use an LLM Router?

In a standard agentic architecture, developers use an LLM as a "Router" (e.g., prompting it with *"If the user asks about Python, use the web search. If they ask about employee policies, use the internal database."*)

This traditional approach has a major flaw: **It ignores observability and prevents self-healing.** If an LLM router hallucinates, chooses the wrong tool, or fails silently, a developer has to manually debug the traces and rewrite the prompt. 

TracePilot fixes this by implementing an **Explore/Exploit Economic Memory System** driven by trace data.

## How TracePilot Learns (Explore vs. Exploit)

TracePilot routes queries based on a dynamic "Confidence Score" calculated from four observability metrics: **Success Rate, Cost, Latency, and Recovery Cost**.

1. **Explore Mode:** When the system encounters a new type of query, or if a previously reliable tool starts failing, its confidence score drops below the `EXPLOIT_THRESHOLD` (0.50). The agent enters "Explore Mode," autonomously cycling through unknown tools (like `web_search`, `uploaded_documents`, or `internal_kb`) to test their efficacy.
2. **The Phoenix Auditor:** When the agent explores the wrong tool (e.g., trying to find an internal employee handbook on the public web), the tool returns an "Access Denied" error. The **Phoenix Trace Auditor** programmatically scrapes the OpenInference telemetry traces, identifies these hidden failures, and penalizes the tool's confidence score in the SQLite database.
3. **Exploit Mode:** Once the agent explores and finds the *correct* tool, the successful execution trace boosts that tool's confidence score above the threshold. The agent locks into "Exploit Mode," routing all future queries of that category instantly to the optimal tool, maximizing speed and minimizing API costs.

This self-healing loop means TracePilot literally learns how to do its job by reading its own observability logs!

## Tech Stack
- **Google Agent Development Kit (ADK):** Powers the core agent logic and orchestrates tool execution.
- **Google Gemini (gemini-2.5-flash):** The underlying intelligence engine.
- **Arize Phoenix / OpenInference:** Captures high-fidelity traces of LLM executions, tool calls, and latency metrics. The backend programmatically audits these traces using the Phoenix SDK.
- **FastAPI:** Serves the backend orchestration endpoints and the UI.
- **SQLite:** Powers the lightweight "Economic Memory" system without heavy database infrastructure.
- **Google Cloud Run:** Hosts the production deployment.

## Demo Scenarios

When running the TracePilot demo, you can watch the agent learn in real-time:
1. Ask a public query like "What is Python?". The agent will successfully route to `web_search`.
2. Ask an internal query like "Find employee handbook section 8.1".
3. Watch the agent mistakenly attempt to use the `web_search` and fail.
4. Click **Run Phoenix Auditor**. The system will analyze the traces, detect the hidden tool failure, and penalize `web_search` for internal queries.
5. Ask another internal query like "Find employee handbook section 7.3". Watch the agent enter **Explore Mode**, systematically testing `uploaded_documents` and `internal_kb` until it self-heals and finds the correct route!

## Running Locally

1. Set up a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Export your Phoenix API keys:
   ```bash
   export PHOENIX_API_KEY="your-api-key"
   ```

3. Run the TracePilot server:
   ```bash
   uvicorn tracepilot.api:app --host 0.0.0.0 --port 5000 --reload
   ```

4. Open `http://localhost:5000` in your browser.
