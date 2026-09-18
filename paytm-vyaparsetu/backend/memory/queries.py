"""
memory/queries.py
Grounded semantic query synthesizers against the Cognee Knowledge Graph.
"""

from memory.graph_client import search_graph
from core.logging import get_logger

logger = get_logger("memory.queries")

async def query_rate_trend(dataset_name: str, sku: str, distributor_name: str) -> str:
    """
    Queries historical prices of a specific SKU from a distributor.
    Returns a synthesized narrative of the price trend.
    """
    logger.info(f"Querying rate trend for '{sku}' from '{distributor_name}' in '{dataset_name}'")
    
    query = f"What is the historical price and rate trend for the item '{sku}' from distributor '{distributor_name}'?"
    
    try:
        # cognee.search returns a string (the synthesized answer)
        result = await search_graph(dataset_name, query)
        
        # If the result is a list (e.g. raw nodes), we could format it. 
        # Usually Cognee handles the RAG synthesis if configured correctly.
        if isinstance(result, list):
            return f"Found {len(result)} relevant records for {sku}."
            
        return str(result)
        
    except Exception as e:
        logger.error(f"Rate trend query failed: {e}")
        return "Could not determine the historical rate trend due to an error."

async def query_grounded_qa(dataset_name: str, question: str) -> str:
    """
    General semantic search across the merchant's isolated dataset to synthesize answers.
    """
    logger.info(f"Querying grounded QA in '{dataset_name}': '{question}'")
    
    try:
        result = await search_graph(dataset_name, question)
        if isinstance(result, list):
            return "\n".join([str(r) for r in result])
        return str(result)
        
    except Exception as e:
        logger.error(f"Grounded QA query failed: {e}")
        return "I am unable to answer that question right now due to an internal error."
