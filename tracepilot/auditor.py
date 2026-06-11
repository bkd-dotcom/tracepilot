"""TracePilot Auditor — ADK Agent using Arize Phoenix MCP to evaluate traces."""

import asyncio
import json
import os
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.runners import InMemoryRunner
from google.genai import types

from tracepilot.config import MODEL_NAME
from tracepilot.memory import get_confidence_table, update_confidence_from_audit, _recalculate_all, get_db
from tracepilot.display import print_confidence_table, print_audit_summary

async def async_run_audit(db_path: str = "tracepilot_memory.db"):
    from rich.console import Console
    console = Console()
    
    console.print("\n[bold cyan]═══ TracePilot MCP Auditor ═══[/bold cyan]")
    console.print("[dim]Spinning up Auditor Agent with Arize Phoenix MCP...[/dim]\n")
    
    from mcp.client.stdio import StdioServerParameters
    
    mcp_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=[
                    "tracepilot/mcp_server.py"
                ]
            )
        ),
    )
    
    # 2. Instantiate the Auditor Agent
    auditor_agent = LlmAgent(
        model=MODEL_NAME,
        name="phoenix_auditor",
        instruction="""
You are the TracePilot Auditor Agent. Your job is to use the Phoenix MCP server to query recent traces.
Call your tool to fetch traces. 
Analyze the traces for any tool span where the output contains the word 'error' or 'Access Denied'.
If you find a failing tool, you must penalize it by outputting a JSON object exactly like this:
```json
{
    "penalties": [
        {"tool_name": "internal_kb", "reason": "Access denied error"}
    ]
}
```
If there are no errors, output {"penalties": []}.
Output ONLY the JSON and nothing else.
""",
        tools=[mcp_toolset]
    )

    runner = InMemoryRunner(agent=auditor_agent, app_name="auditor")
    session = await runner.session_service.create_session(state={}, app_name="auditor", user_id="admin")
    
    result_text = ""
    console.print("[dim]Auditor Agent is querying Phoenix via MCP...[/dim]")
    try:
        async for event in runner.run_async(
            user_id="admin",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text="URGENT: Fetch the traces immediately. Find any tool failures and ONLY return the JSON array of penalties. Be extremely concise to minimize latency. Do not explain.")]
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        result_text += p.text
    except Exception as e:
        console.print(f"[red]Error running MCP Agent: {e}[/red]")
        raise e

    # Parse JSON output
    corrections_made = 0
    try:
        # Strip markdown code blocks if any
        clean_text = result_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        penalties = data if isinstance(data, list) else data.get("penalties", [])
        for penalty in penalties:
            tool_name = penalty.get("tool_name")
            if tool_name:
                with get_db(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE economic_memory 
                        SET successful_runs = MAX(0, successful_runs - 1)
                        WHERE tool_name = ?
                    ''', (tool_name,))
                corrections_made += 1
    except Exception as e:
        console.print(f"[yellow]Could not parse Auditor Agent JSON output: {e}[/yellow]\nOutput was: {result_text}")
        
    return corrections_made

def run_audit(db_path: str = "tracepilot_memory.db") -> None:
    """Query Phoenix traces via MCP Agent and update Economic Memory confidence scores."""
    from rich.console import Console
    console = Console()
    
    before = get_confidence_table(db_path)
    
    corrections_made = asyncio.run(async_run_audit(db_path))
    
    from tracepilot.events import emit_event
    if corrections_made > 0:
        console.print(f"[yellow]⚠️ MCP Audit found {corrections_made} hidden tool failures! Correcting memory...[/yellow]")
        emit_event(
            type="learning",
            title="Memory Correction",
            description=f"MCP Auditor Agent found {corrections_made} hidden LLM failure(s). Confidence scores recalculated.",
            metrics={"corrections": corrections_made}
        )
    else:
        console.print("[green]✅ MCP Audit complete. No new hidden tool failures found.[/green]")
        
    console.print("[dim]Recalculating confidence scores from run history...[/dim]\n")
    
    # Recalculate all confidence scores from the recorded runs
    _recalculate_all(db_path)
    
    # Get after state  
    after = get_confidence_table(db_path)
    
    # Print comparison
    print_audit_summary(before, after)
    
    # Print final table
    console.print("\n[bold]Current Economic Memory:[/bold]")
    print_confidence_table(after)
