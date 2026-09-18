from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import timedelta
from db.models import InsightCache
from core.logging import get_logger

logger = get_logger("db.insight_cache_repo")

def get_cached_insight(db: Session, cache_key: str) -> Optional[InsightCache]:
    """Retrieve an active (non-stale) insight from the cache."""
    cache_entry = db.query(InsightCache).filter(
        InsightCache.cache_key == cache_key,
        InsightCache.stale_after > func.now()
    ).first()
    
    if cache_entry:
        logger.info(f"🔍 [DB Read] Cache HIT for key: {cache_key}")
    else:
        logger.info(f"🔍 [DB Read] Cache MISS for key: {cache_key}")
        
    return cache_entry

def save_insight(
    db: Session, 
    cache_key: str, 
    merchant_id: str, 
    insight_type: str, 
    result: dict, 
    ttl_hours: int = 24
) -> InsightCache:
    """Upsert an insight into the cache with a specified TTL."""
    # Check if exists
    cache_entry = db.query(InsightCache).filter(InsightCache.cache_key == cache_key).first()
    
    if cache_entry:
        cache_entry.result = result
        cache_entry.stale_after = func.now() + timedelta(hours=ttl_hours)
        cache_entry.generated_at = func.now()
        logger.info(f"💾 [DB Write] UPDATED cache entry for key: {cache_key}")
    else:
        cache_entry = InsightCache(
            cache_key=cache_key,
            merchant_id=merchant_id,
            insight_type=insight_type,
            result=result,
            stale_after=func.now() + timedelta(hours=ttl_hours)
        )
        db.add(cache_entry)
        logger.info(f"💾 [DB Write] INSERTED cache entry for key: {cache_key}")
        
    db.commit()
    db.refresh(cache_entry)
    return cache_entry
