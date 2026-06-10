"""TracePilot Auditor — queries Phoenix traces and updates Economic Memory."""

from phoenix.client import Client
from tracepilot.config import PHOENIX_ENDPOINT, PROJECT_NAME, TOOL_COSTS
from tracepilot.memory import get_confidence_table, update_confidence_from_audit, _recalculate_all, get_db
from tracepilot.display import print_confidence_table, print_audit_summary


def run_audit(db_path: str = "tracepilot_memory.db") -> None:
    """Query Phoenix traces and update Economic Memory confidence scores."""
    from rich.console import Console
    console = Console()
    
    console.print("\n[bold cyan]═══ TracePilot Auditor ═══[/bold cyan]")
    console.print("[dim]Querying Phoenix for trace data...[/dim]\n")
    
    # Get before state
    before = get_confidence_table(db_path)
    
    try:
        import os
        os.environ.pop("PHOENIX_CLIENT_HEADERS", None)
        os.environ.pop("PHOENIX_COLLECTOR_ENDPOINT", None)
        client = Client(base_url="https://app.phoenix.arize.com", api_key="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MSJ9.nf7V-hnJXR3mtIBYvTc7KHaAjclvuEhpDFa8A5aCsPY")
        # Query spans from the tracepilot project
        spans_df = client.spans.get_spans_dataframe(
            project_name=PROJECT_NAME,
        )
        
        if spans_df is None or spans_df.empty:
            console.print("[yellow]No traces found in Phoenix. Run some queries first.[/yellow]")
            return
            
        from tracepilot.memory import get_last_reset_time
        import pandas as pd
        last_reset = get_last_reset_time()
        spans_df['start_time'] = pd.to_datetime(spans_df['start_time'], utc=True)
        spans_df = spans_df[spans_df['start_time'] >= pd.to_datetime(last_reset, utc=True)]
        
        if spans_df.empty:
            console.print("[yellow]No new traces since last reset.[/yellow]")
            return
        
        console.print(f"[green]Found {len(spans_df)} spans in Phoenix[/green]")
        
        # Analyze spans for insights
        # Look for TOOL spans and their success/failure
        if "attributes.tool.name" in spans_df.columns:
            tool_spans = spans_df[spans_df["attributes.tool.name"].notnull()]
        else:
            tool_spans = spans_df[spans_df.get("span_kind", "") == "TOOL"] if "span_kind" in spans_df.columns else spans_df
        
        console.print(f"[dim]Analyzed {len(tool_spans)} tool spans[/dim]")
        
        # In a real app we'd map trace IDs to query IDs. For the demo, we just look at the last few tool runs.
        # If a tool span output contains '"status": "error"', we force the confidence down.
        corrections_made = 0
        if "attributes.output.value" in tool_spans.columns:
            for idx, row in tool_spans.iterrows():
                output = str(row.get("attributes.output.value", ""))
                
                tool_name = str(row.get("attributes.tool.name", ""))
                if not tool_name:
                    tool_name = str(row.get("name", "")).replace("execute_tool ", "")
                
                if '"status": "error"' in output or '"status":"error"' in output or "'status': 'error'" in output or "'status':'error'" in output:
                    # We found a tool error that the agent might have hallucinated as a success!
                    # Penalize confidence
                    # For demo purposes, we will hardcode the category deduction since we don't have trace linking
                    category = "internal" if "employee" in output or "internal" in output else "public"
                    
                    # Update DB directly to mark a failure
                    with get_db(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE economic_memory 
                            SET successful_runs = MAX(0, successful_runs - 1)
                            WHERE tool_name = ?
                        ''', (tool_name,))
                    corrections_made += 1
                    
        from tracepilot.events import emit_event
        if corrections_made > 0:
            console.print(f"[yellow]⚠️ Audit found {corrections_made} hidden tool failures! Correcting memory...[/yellow]")
            emit_event(
                type="learning",
                title="Memory Correction",
                description=f"Auditor found {corrections_made} hidden LLM failure(s). Confidence scores recalculated.",
                metrics={"corrections": corrections_made}
            )
        
        console.print("[dim]Recalculating confidence scores from run history...[/dim]\n")
        
    except Exception as e:
        console.print(f"[yellow]Phoenix query returned: {e}[/yellow]")
        console.print("[dim]Falling back to local Economic Memory data for audit...[/dim]\n")
    
    # Recalculate all confidence scores from the recorded runs
    _recalculate_all(db_path)
    
    # Get after state  
    after = get_confidence_table(db_path)
    
    # Print comparison
    print_audit_summary(before, after)
    
    # Print final table
    console.print("\n[bold]Current Economic Memory:[/bold]")
    print_confidence_table(after)
