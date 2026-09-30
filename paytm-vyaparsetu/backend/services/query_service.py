import hashlib
import time
from sqlalchemy.orm import Session
from db.repositories import insight_cache_repo
from core.logging import get_logger
from core.llm_client import run_grounded_qa_agent

logger = get_logger("services.query_service")

async def answer_grounded_question(db: Session, merchant_id: str, question: str) -> dict:
    """Answers a question using LLM Tool Calling and semantic caching."""
    
    # 1. Deterministic Cache Key (for repeated identical questions)
    question_hash = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:12]
    cache_key = f"qa_agent_{merchant_id}_{question_hash}"
    
    # 2. Check Cache
    cached = insight_cache_repo.get_cached_insight(db, cache_key)
    if cached:
        logger.info(f"⚡ [Query Service] Cache HIT for question: '{question[:30]}...'")
        result_data = cached.result
        return {
            "answer": result_data.get("answer", ""),
            "data": result_data.get("data"),
            "tool_used": result_data.get("tool_used"),
            "source": "CACHE",
            "generated_in_ms": 0
        }
        
    logger.info(f"🌐 [Query Service] Cache MISS. Routing to LLM Engine for: '{question[:30]}...'")
    start_time = time.time()
    
    # 3. Call Agent
    agent_result = await run_grounded_qa_agent(db, merchant_id, question)
        
    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"✅ [Query Service] Query completed in {elapsed_ms}ms")
    
    final_result = {
        "answer": agent_result.get("answer", ""),
        "data": agent_result.get("data"),
        "tool_used": agent_result.get("tool_used"),
        "source": "LIVE",
        "generated_in_ms": elapsed_ms
    }
    
    # 4. Persist to cache
    if agent_result.get("status") != "error":
        insight_cache_repo.save_insight(
            db=db,
            cache_key=cache_key,
            merchant_id=merchant_id,
            insight_type="QA_ANSWER",
            result={
                "answer": final_result["answer"],
                "data": final_result["data"],
                "tool_used": final_result["tool_used"]
            }
        )
    
    return final_result
