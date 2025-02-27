import asyncio
import aiohttp

async def fetch_csv(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
        
async def incremental_read(response):
    line = await response.content.readline()
    while line:
        print(f"line: {line}")
        yield line
        line = await response.content.readline()
    
    

if __name__ == '__main__':
    url = 'http://localhost:8000/solr1.csv'
    loop = asyncio.get_event_loop()
    csv = loop.run_until_complete(fetch_csv(url))
    print(csv)