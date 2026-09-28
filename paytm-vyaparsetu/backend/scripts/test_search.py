import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

os.environ["COGNEE_API_URL"] = settings.COGNEE_API_URL
os.environ["COGNEE_API_KEY"] = settings.COGNEE_API_KEY

import cognee
from cognee import SearchType

async def test():
    print("Connecting to Cognee Cloud...")
    if hasattr(cognee, "serve"):
        await cognee.serve(url=settings.COGNEE_API_URL, api_key=settings.COGNEE_API_KEY)
    
    print("Executing search for 'Amul'...")
    print(f"Available SearchTypes: {dir(SearchType)}")
    res = await cognee.search(query_text="Amul", datasets=["merchant_mer_gupta01"])
    print("\n--- SEARCH RESULTS ---")
    print(res)
    print("----------------------")

if __name__ == "__main__":
    asyncio.run(test())
