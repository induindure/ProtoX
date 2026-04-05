import sys
sys.path.insert(0, ".")

import asyncio
from app.agents.proto_idea import proto_idea_agent

async def test():
    print("calling gemini...")
    try:
        result = await proto_idea_agent.generate("healthcare", "web app", "")
        print("SUCCESS:", result)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

asyncio.run(test())