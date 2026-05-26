import asyncio
from providers.finnhub_provider import FinnhubProvider
async def main():
    provider = FinnhubProvider()
    print(await provider.get_company_overview("AAPL"))
    await provider.close()
asyncio.run(main())
