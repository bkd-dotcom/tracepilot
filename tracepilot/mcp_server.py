from mcp.server.fastmcp import FastMCP
from phoenix.client import Client
import pandas as pd
import json

# Initialize FastMCP Server
mcp = FastMCP("PhoenixTraceAuditor")
client = Client()

@mcp.tool()
def get_recent_tool_executions(limit: int = 5) -> str:
    """
    Fetches the most recent tool executions from the Arize Phoenix trace backend.
    Returns a JSON string containing the tool names and their raw string outputs.
    Analyze this output to find hidden 'Access Denied' or 'Error' failures.
    """
    try:
        import sqlite3
        import os
        import json
        
        db_path = os.path.expanduser("~/.phoenix/phoenix.db")
        if not os.path.exists(db_path):
            return "[]"
            
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, attributes 
                FROM spans 
                WHERE span_kind = 'TOOL' OR name LIKE 'execute_tool%'
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            
        results = []
        for row in rows:
            name = row[0]
            try:
                attributes = json.loads(row[1]) if row[1] else {}
            except Exception:
                attributes = {}
            
            # Correctly extract from nested dicts (not flat dotted keys)
            tool_obj = attributes.get("tool", {})
            tool_name = tool_obj.get("name", name).replace("execute_tool ", "") if isinstance(tool_obj, dict) else name
            
            output_obj = attributes.get("output", {})
            output_val_raw = output_obj.get("value", "") if isinstance(output_obj, dict) else ""
            # The value itself is a JSON string — parse it to get the actual tool result
            try:
                inner = json.loads(output_val_raw) if output_val_raw else {}
                # Determine status from the parsed result
                has_error = inner.get("status") == "error" or "error" in str(inner.get("type", "")).lower()
                output_summary = f"status={inner.get('status', 'success')}, source={inner.get('source', tool_name)}"
            except Exception:
                has_error = "error" in output_val_raw.lower()[:100]
                output_summary = output_val_raw[:200]
            
            # Also check the span-level error attribute
            error_attr = attributes.get("error", {})
            if isinstance(error_attr, dict) and error_attr.get("type"):
                has_error = True
                output_summary = f"TOOL_ERROR: {error_attr.get('type')}"
            
            results.append({
                "tool_name": tool_name,
                "has_error": has_error,
                "output": output_summary
            })
            
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()
