import hashlib
import time
import asyncio
from sqlalchemy.orm import Session
from db.models import Merchant
from db.repositories import insight_cache_repo
from memory import graph_client
from core.logging import get_logger
from core.errors import AppException, ErrorCode

logger = get_logger("services.query_service")

async def answer_grounded_question(db: Session, merchant_id: str, question: str) -> dict:
    """Answers a question using Cache first, falling back to live Cognee Cloud."""
    
    # 1. Deterministic Cache Key
    question_hash = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:12]
    cache_key = f"qa_{merchant_id}_{question_hash}"
    
    # 2. Check Cache
    cached = insight_cache_repo.get_cached_insight(db, cache_key)
    if cached:
        logger.info(f"⚡ [Query Service] Cache HIT for question: '{question[:30]}...'")
        return {
            "answer": cached.result.get("answer", ""),
            "source": "CACHE",
            "generated_in_ms": 0
        }
        
    logger.info(f"🌐 [Query Service] Cache MISS. Routing to Live Cloud for: '{question[:30]}...'")
    start_time = time.time()
    
    # 3. Fetch dataset name
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
    if not merchant:
        raise AppException(
            code=ErrorCode.MERCHANT_NOT_FOUND,
            message="Merchant not found",
            status_code=404
        )
        
    dataset_name = merchant.cognee_dataset
    
    # 4. Live Query
    try:
        # We need to await search_graph since it's an async function wrapper around cognee SDK
        answer = await graph_client.search_graph(dataset_name=dataset_name, query=question)
    except Exception as e:
        logger.error(f"❌ [Query Service] Live query failed: {str(e)}")
        raise AppException(
            code="CLOUD_QUERY_FAILED",
            message="Failed to query knowledge graph",
            status_code=500
        )
        
    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"✅ [Query Service] Live query completed in {elapsed_ms}ms")
    
    # Format answer if it's a list
    if isinstance(answer, list):
        # Convert list of nodes/results to a string block or assume cognee returns formatted string
        answer_text = "\n".join([str(item) for item in answer])
    else:
        answer_text = str(answer)
        
    # 5. Persist to cache
    result_dict = {"answer": answer_text}
    insight_cache_repo.save_insight(
        db=db,
        cache_key=cache_key,
        merchant_id=merchant_id,
        insight_type="QA_ANSWER",
        result=result_dict
    )
    
    return {
        "answer": answer_text,
        "source": "LIVE",
        "generated_in_ms": elapsed_ms
    }
