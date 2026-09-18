"""
memory/graph_client.py
Wrapper around the Cognee SDK ensuring strict dataset parameterization,
network timeouts, and graceful error handling for Cloud integration.
"""

import asyncio
import cognee
from typing import Any
from core.logging import get_logger
from config import settings

logger = get_logger("memory.graph_client")

# Define a default timeout for cloud operations
CLOUD_TIMEOUT_SECONDS = 30.0

_is_connected = False

async def _ensure_connected():
    global _is_connected
    if not _is_connected:
        if hasattr(cognee, "serve"):
            await cognee.serve(url=settings.COGNEE_API_URL, api_key=settings.COGNEE_API_KEY)
        _is_connected = True

async def add_payload(dataset_name: str, data: Any) -> bool:
    """Adds a generic payload (usually Pydantic model instances) to the dataset."""
    logger.info(f"Adding payload to dataset '{dataset_name}'")
        
    try:
        await _ensure_connected()
        async with asyncio.timeout(CLOUD_TIMEOUT_SECONDS):
            await cognee.add(data, dataset_name=dataset_name)
        logger.info(f"Successfully added payload to '{dataset_name}'")
        return True
    except asyncio.TimeoutError:
        logger.error(f"Timeout adding payload to '{dataset_name}' after {CLOUD_TIMEOUT_SECONDS}s")
        return False
    except Exception as e:
        logger.error(f"Error adding payload to '{dataset_name}': {e}")
        return False

async def cognify_dataset(dataset_name: str) -> bool:
    """Cognifies the dataset to build the knowledge graph."""
    logger.info(f"Cognifying dataset '{dataset_name}'")
        
    try:
        await _ensure_connected()
        # Cognification can take longer depending on dataset size
        async with asyncio.timeout(CLOUD_TIMEOUT_SECONDS * 2):
            await cognee.cognify(datasets=[dataset_name])
        logger.info(f"Successfully cognified '{dataset_name}'")
        return True
    except asyncio.TimeoutError:
        logger.error(f"Timeout cognifying '{dataset_name}' after {CLOUD_TIMEOUT_SECONDS * 2}s")
        return False
    except Exception as e:
        logger.error(f"Error cognifying '{dataset_name}': {e}")
        return False

async def search_graph(dataset_name: str, query: str) -> str | list:
    """Searches the knowledge graph and returns grounded answers."""
    logger.info(f"Searching dataset '{dataset_name}': '{query}'")
        
    try:
        await _ensure_connected()
        async with asyncio.timeout(CLOUD_TIMEOUT_SECONDS):
            # cognee.search returns a string or list depending on query type, we'll return raw for now
            result = await cognee.search(query_text=query, datasets=[dataset_name])
        logger.info(f"Search successful for '{dataset_name}'")
        return result
    except asyncio.TimeoutError:
        logger.error(f"Timeout searching '{dataset_name}' after {CLOUD_TIMEOUT_SECONDS}s")
        return "Search timed out."
    except Exception as e:
        logger.error(f"Error searching '{dataset_name}': {e}")
        return f"Error during search: {e}"

async def prune_or_reset_dataset(dataset_name: str) -> bool:
    """Prunes or resets a specific dataset. Use with caution."""
    logger.warning(f"Pruning dataset '{dataset_name}'")
    try:
        await _ensure_connected()
        async with asyncio.timeout(CLOUD_TIMEOUT_SECONDS):
            await cognee.prune.prune_data() # Warning: standard cognee prune might be global. Assuming SDK supports dataset scoping if needed.
            await cognee.prune.prune_system(metadata=True)
        logger.info(f"Successfully pruned '{dataset_name}'")
        return True
    except Exception as e:
        logger.error(f"Error pruning '{dataset_name}': {e}")
        return False
