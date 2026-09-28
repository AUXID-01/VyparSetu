import asyncio
import os
import sys

# Add backend directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# Force Cloud Connection
os.environ["COGNEE_API_URL"] = settings.COGNEE_API_URL
os.environ["COGNEE_API_KEY"] = settings.COGNEE_API_KEY

import cognee

async def test_document_ingestion():
    print("Connecting to Cognee Cloud...")
    if hasattr(cognee, "serve"):
        await cognee.serve(url=settings.COGNEE_API_URL, api_key=settings.COGNEE_API_KEY)
    
    dataset_name = "merchant_mer_gupta01"
    
    # Passing a raw string creates an Unstructured Document in Cognee, 
    # which increments the 'Documents' counter in the UI.
    raw_text = "VyaparSetu is an amazing app. We recently onboarded Amul Dairy as a main distributor for our merchant Ramesh Gupta."
    
    print(f"Adding unstructured text document to dataset '{dataset_name}'...")
    await cognee.add(raw_text, dataset_name=dataset_name)
    
    print("Document added! Cognifying...")
    await cognee.cognify(datasets=[dataset_name])
    print("\n✅ Success! Go to the Cognee Dashboard -> Datasets tab.")
    print(f"You should now see the 'Documents' count > 0 for {dataset_name}.")

if __name__ == "__main__":
    asyncio.run(test_document_ingestion())
