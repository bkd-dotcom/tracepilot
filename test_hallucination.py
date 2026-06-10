import asyncio
from dotenv import load_dotenv
load_dotenv()
from tracepilot.tools import web_search
from tracepilot.orchestrator import _create_agent, _run_agent

async def main():
    agent = _create_agent(web_search)
    for i in range(5):
        res, succ = await _run_agent(agent, "Find employee handbook section 7.3")
        print(f"Run {i}: {res}")

if __name__ == "__main__":
    asyncio.run(main())
