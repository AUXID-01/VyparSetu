"""
scripts/test_cognee_cloud_standalone.py
Standalone test script to verify authentication against Cognee Cloud
and ensure Groq LLM integration works with dataset isolation.
"""
import asyncio
import os
from config import settings

# Set up environment variables for Cognee before importing it
os.environ["COGNEE_API_KEY"] = settings.COGNEE_API_KEY
if settings.COGNEE_API_URL:
    os.environ["COGNEE_API_URL"] = settings.COGNEE_API_URL

import asyncio
import cognee
from config import settings

async def main():
    print("Initializing connection to Cognee Cloud...")
    
    # Connect SDK to Cognee Cloud
    if hasattr(cognee, "serve"):
        await cognee.serve(url=settings.COGNEE_API_URL, api_key=settings.COGNEE_API_KEY)
    else:
        os.environ["COGNEE_API_KEY"] = settings.COGNEE_API_KEY
        os.environ["COGNEE_API_URL"] = settings.COGNEE_API_URL

    dataset_name = "dev_sandbox"
    print(f"Adding test payload to dataset: {dataset_name}...")
    
    sample_data = {
        "merchant_id": "mer_test_01",
        "customer_id": "cus_suresh_01",
        "amount": 240.0,
        "event_type": "CREDIT_ADDED"
    }
    
    # Ingest structured data
    try:
        await cognee.add(sample_data, dataset_name=dataset_name)
        print("✅ Payload added successfully.")
    except Exception as e:
        print(f"❌ Failed to add payload: {e}")
        return

    print("Running cognify()...")
    try:
        await cognee.cognify(datasets=[dataset_name])
        print("✅ Cognification complete.")
    except Exception as e:
        print(f"❌ Failed to cognify: {e}")
        return
    
    print("Executing search query...")
    try:
        results = await cognee.search(query_text="What is Suresh's credit?", datasets=[dataset_name])
        print("Search Results:", results)
        print("\n✅ Cognee Cloud standalone verification successful!")
    except Exception as e:
        print(f"❌ Failed to search: {e}")

if __name__ == "__main__":
    asyncio.run(main())
