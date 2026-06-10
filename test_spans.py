import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

from tracepilot.tracing import init_tracing
init_tracing()

from tracepilot.orchestrator import run_query
import phoenix.client

async def main():
    print(await run_query("What is the employee handbook?"))
    
    client = phoenix.client.Client(base_url="http://127.0.0.1:6006")
    df = client.spans.get_spans_dataframe(project_name="tracepilot")
    
    if df is not None:
        for _, row in df.iterrows():
            print(f"Span: {row.get('name')}, Kind: {row.get('span_kind')}, Attributes: {list(row.keys())}")
            
if __name__ == "__main__":
    asyncio.run(main())
