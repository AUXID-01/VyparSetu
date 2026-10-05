"""
backend/memory/__init__.py
Compatibility stubs for legacy Cognee memory references.
"""

def get_dataset_for_merchant(merchant_id: str) -> str:
    return f"merchant_{merchant_id}"

async def remember_transaction(dataset: str, payload: dict) -> None:
    pass

async def cognify_dataset(dataset: str) -> None:
    pass
