import asyncio
from research_agent.regulatory_crawler import aggregate_regulatory_intelligence

async def run():
    res = await aggregate_regulatory_intelligence("Sharma Textile Mills Pvt. Ltd.")
    print(res)

asyncio.run(run())
