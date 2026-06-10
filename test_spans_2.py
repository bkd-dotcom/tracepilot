import asyncio
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

import phoenix.client

client = phoenix.client.Client(base_url="http://127.0.0.1:6006")
df = client.spans.get_spans_dataframe(project_name="tracepilot")
if df is not None:
    for idx, row in df.iterrows():
        name = row.get("name")
        kind = row.get("span_kind")
        tool_name = row.get("attributes.tool.name")
        output_val = row.get("attributes.output.value")
        print(f"Name: {name}, Kind: {kind}, ToolName: {tool_name}, Output: {str(output_val)[:50]}")
