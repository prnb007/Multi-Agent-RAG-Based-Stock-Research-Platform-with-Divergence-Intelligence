import json
import dataclasses
from dotenv import load_dotenv
load_dotenv()
from narrative.narrative_service import narrative_service
from narrative.narrative_service import narrative_service
import asyncio

async def main():
    signals = await narrative_service.get_narrative_timeline("AAPL")
    out = {
        "ticker":   "AAPL",
        "quarters": [dataclasses.asdict(s) for s in signals],
        "summary": {
            "total_quarters": len(signals),
            "tone_trend": [s.management_tone for s in signals],
            "ai_trend":   [s.ai_monetization for s in signals],
            "margin_trend": [s.margin_language for s in signals],
        }
    }
    print(json.dumps(out, indent=2))

asyncio.run(main())
