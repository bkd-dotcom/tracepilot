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
            attributes = json.loads(row[1]) if row[1] else {}
            
            tool_name = attributes.get("tool.name", name).replace("execute_tool ", "")
            output_val = str(attributes.get("output.value", ""))
            
            results.append({
                "tool_name": tool_name,
                "output": output_val[:200]  # truncate to prevent massive payload
            })
            
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()
