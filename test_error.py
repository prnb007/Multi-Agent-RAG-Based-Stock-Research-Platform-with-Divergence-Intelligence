import asyncio
from dotenv import load_dotenv
load_dotenv()
from narrative.narrative_service import narrative_service

async def main():
    try:
        await narrative_service.get_narrative_timeline("AAPL", force_refresh=True)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
