import asyncio
from scrappers.scrapAmazon import fluxo_completo_amazon

async def main():
    await fluxo_completo_amazon()

if __name__ == "__main__":
    asyncio.run(main())