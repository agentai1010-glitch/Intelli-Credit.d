import urllib.parse
import httpx
import asyncio

async def test_rss():
    q = "Zee Entertainment Enterprises Ltd. NCLT insolvency proceedings"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=en-IN&gl=IN&ceid=IN:en"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        print("RAW RSS START-------------")
        print(res.text[:1500])
        print("-------------RAW RSS END")

if __name__ == "__main__":
    asyncio.run(test_rss())
