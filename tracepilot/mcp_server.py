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
        df = client.spans.get_spans_dataframe(project_name="tracepilot")
        if df is None or df.empty:
            return "[]"
            
        if "attributes.tool.name" in df.columns:
            tool_spans = df[df["attributes.tool.name"].notnull()]
        else:
            if "span_kind" in df.columns:
                tool_spans = df[df["span_kind"] == "TOOL"]
            else:
                tool_spans = df
                
        # Sort chronologically to get the most recent ones at the tail
        if "start_time" in tool_spans.columns:
            tool_spans = tool_spans.sort_values(by="start_time")
            
        recent = tool_spans.tail(limit).fillna("").to_dict(orient="records")
        
        results = []
        for r in recent:
            tool_name = str(r.get("attributes.tool.name", r.get("name", "Unknown"))).replace("execute_tool ", "")
            output_val = str(r.get("attributes.output.value", ""))
            
            results.append({
                "tool_name": tool_name,
                "output": output_val[:200]  # truncate to prevent massive payload
            })
            
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()
