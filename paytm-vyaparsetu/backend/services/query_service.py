import base64
import hashlib
import time
from sqlalchemy.orm import Session
from db.repositories import insight_cache_repo
from core.logging import get_logger
from core.llm_client import run_grounded_qa_agent
import sarvam

logger = get_logger("services.query_service")

async def answer_grounded_question(db: Session, merchant_id: str, question: str) -> dict:
    """Answers a question using Single-Hop LLM Tool Calling, semantic caching, and Sarvam TTS synthesis."""
    
    # 1. Deterministic Cache Key (for repeated identical questions)
    question_hash = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:12]
    cache_key = f"qa_agent_{merchant_id}_{question_hash}"
    
    # 2. Check Cache
    cached = insight_cache_repo.get_cached_insight(db, cache_key)
    if cached:
        logger.info(f"⚡ [Query Service] Cache HIT for question: '{question[:30]}...'")
        result_data = cached.result or {}
        return {
            "answer": result_data.get("answer", ""),
            "answer_audio_b64": result_data.get("answer_audio_b64", ""),
            "data": result_data.get("data"),
            "tool_used": result_data.get("tool_used"),
            "source": "CACHE",
            "generated_in_ms": 0
        }
        
    logger.info(f"🌐 [Query Service] Cache MISS. Routing to Single-Hop LLM Engine for: '{question[:30]}...'")
    start_time = time.time()
    
    # 3. Call Agent (Single-Hop direct Indic understanding + tool execution + spoken synthesis)
    agent_result = await run_grounded_qa_agent(db, merchant_id, question)
    answer_text = agent_result.get("answer", "")
    
    # 4. Generate Spoken Voice Audio via Sarvam TTS
    answer_audio_b64 = ""
    if answer_text and agent_result.get("status") != "error":
        try:
            logger.info(f"🎙️ [Query Service] Synthesizing speech for answer: '{answer_text[:40]}...'")
            audio_bytes = sarvam.synthesize_speech(text=answer_text)
            if audio_bytes and len(audio_bytes) > 100:
                answer_audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                logger.info(f"🎙️ [Query Service] TTS generated {len(audio_bytes)} bytes audio (b64 length: {len(answer_audio_b64)})")
        except Exception as exc:
            logger.warning(f"⚠️ [Query Service] Failed to synthesize audio via Sarvam: {exc}")
            answer_audio_b64 = ""

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"✅ [Query Service] Query completed in {elapsed_ms}ms")
    
    final_result = {
        "answer": answer_text,
        "answer_audio_b64": answer_audio_b64,
        "data": agent_result.get("data"),
        "tool_used": agent_result.get("tool_used"),
        "source": "LIVE",
        "generated_in_ms": elapsed_ms
    }
    
    # 5. Persist to cache
    if agent_result.get("status") != "error":
        insight_cache_repo.save_insight(
            db=db,
            cache_key=cache_key,
            merchant_id=merchant_id,
            insight_type="QA_ANSWER",
            result={
                "answer": final_result["answer"],
                "answer_audio_b64": final_result["answer_audio_b64"],
                "data": final_result["data"],
                "tool_used": final_result["tool_used"]
            }
        )
    
    return final_result
