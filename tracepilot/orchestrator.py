"""TracePilot orchestrator — routes queries through Economic Memory."""

import asyncio
import time
from typing import Optional

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from tracepilot.config import MODEL_NAME, TOOL_COSTS, DEFAULT_TOOL
from tracepilot.memory import init_db, get_optimal_routing, record_run, get_confidence_table
from tracepilot.tools import internal_kb_search, web_search, uploaded_documents_search
from tracepilot.display import (
    print_confidence_table,
    print_routing_decision,
    print_run_result,
)

# Map tool names to functions
TOOL_MAP = {
    "internal_kb": internal_kb_search,
    "web_search": web_search,
    "uploaded_documents": uploaded_documents_search
}

# Map tool names to alternate tools (for fallback)
FALLBACK_MAP = {
    "internal_kb": "web_search",
    "web_search": "internal_kb",
}


def classify_query(query: str) -> str:
    """Classify a query as 'internal' or 'public' using keyword heuristics."""
    internal_keywords = [
        "employee", "handbook", "policy", "hr", "internal", "company",
        "section", "procedure", "onboarding", "offboarding", "expense",
        "pto", "benefits", "compensation", "performance review",
        "badge", "vpn", "conference room", "it support", "org chart",
        "dress code", "remote work", "equipment", "safety", "retirement",
        "stock option", "complaint",
    ]
    query_lower = query.lower()
    for kw in internal_keywords:
        if kw in query_lower:
            return "internal"
    return "public"


def _create_agent(tool_func) -> Agent:
    """Create an ADK agent with a single tool."""
    return Agent(
        name="tracepilot_agent",
        model=MODEL_NAME,
        instruction=(
            "You are TracePilot, an enterprise assistant. "
            "Use the provided tool to answer the user's question. "
            "Always call the tool first before responding. "
            "If the tool returns an error, you MUST include the exact text 'TOOL_ERROR' somewhere in your response."
        ),
        tools=[tool_func],
    )


async def _run_agent(agent: Agent, query: str) -> tuple[str, bool]:
    """Run an ADK agent and return (response_text, success)."""
    runner = InMemoryRunner(
        agent=agent,
        app_name="tracepilot",
    )
    
    session = await runner.session_service.create_session(
        state={}, app_name="tracepilot", user_id="demo_user"
    )
    
    result_text = ""
    async for event in runner.run_async(
        user_id="demo_user",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=query)]
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            result_text = event.content.parts[0].text or ""
    
    # Determine success: if the tool returned an error, the agent was instructed to output TOOL_ERROR
    success = bool(result_text) and "TOOL_ERROR" not in result_text
    return result_text, success


from tracepilot.events import emit_event

async def run_query(query: str, db_path: str = "tracepilot_memory.db") -> str:
    """Route and execute a query through the Economic Memory system."""
    init_db(db_path)
    
    # Step 1: Classify
    category = classify_query(query)
    
    # Step 2: Get routing decision
    routing = get_optimal_routing(category, db_path)
    selected_tool = routing["tool"]
    confidence = routing["confidence"]
    mode = routing["mode"]
    all_options = routing["all_options"]
    
    # Step 3: Print routing decision with explainability
    print_routing_decision(category, selected_tool, confidence, mode, all_options)
    
    emit_event(
        type="routing",
        title="Routing Decision",
        description=f"Routed query to '{selected_tool}' (Confidence: {confidence:.2f})",
        metrics={"mode": mode, "options": all_options}
    )
    
    # Step 4: Execute with chosen tool
    tool_func = TOOL_MAP[selected_tool]
    agent = _create_agent(tool_func)
    
    start_time = time.time()
    result_text, success = await _run_agent(agent, query)
    primary_latency = time.time() - start_time
    primary_cost = TOOL_COSTS[selected_tool]
    
    recovery_cost = 0.0
    final_tool = selected_tool
    fallback_used = False
    
    # Step 5: Record the result (No fallback per user request)
    record_run(category, selected_tool, success, primary_cost, primary_latency, 0.0, db_path)
    
    # Step 6: Print run result
    print_run_result(
        query=query,
        tool_used=final_tool,
        success=success,
        result=result_text[:200] + "..." if len(result_text) > 200 else result_text,
        latency=primary_latency,
        cost=primary_cost,
        recovery_cost=recovery_cost,
    )
    
    # Step 7: Print confidence table
    rows = get_confidence_table(db_path)
    print_confidence_table(rows)
    
    event_type = "system" if success else "failure"
    emit_event(
        type=event_type,
        title="Execution Complete",
        description=f"Query executed via '{final_tool}' in {primary_latency:.2f}s",
        metrics={
            "latency": primary_latency,
            "cost": primary_cost,
            "recovery_cost": recovery_cost,
            "success": success
        }
    )
    
    return {
        "result_text": result_text,
        "routing": routing,
        "metrics": {
            "latency": primary_latency,
            "cost": primary_cost,
            "recovery_cost": recovery_cost,
            "success": success,
            "tool_used": final_tool
        }
    }
