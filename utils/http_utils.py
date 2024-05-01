import aiohttp

async def fetch_data(url, payload):
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, json=payload)
        return await response.json()