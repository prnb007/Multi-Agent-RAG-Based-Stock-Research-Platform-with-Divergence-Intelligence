import asyncio
from providers.fmp_provider import FMPProvider

async def main():
    provider = FMPProvider()
    print("Overview:", await provider.get_company_overview("AAPL"))
    print("Income:", await provider.get_income_statement("AAPL"))
    print("Balance:", await provider.get_balance_sheet("AAPL"))
    print("Cashflow:", await provider.get_cash_flow("AAPL"))
    await provider.close()

asyncio.run(main())
