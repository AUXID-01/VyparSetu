from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from db.session import SessionLocal
from core.logging import get_logger

logger = get_logger("workers.context")

@contextmanager
def get_worker_db() -> Generator[Session, None, None]:
    """
    Dedicated context manager for background workers and asynchronous loops.
    Ensures:
      1. Every background execution runs on an isolated SessionLocal instance.
      2. Transactions are automatically committed upon clean block exit.
      3. Automatic rollback on unhandled exceptions to prevent connection pool poisoning.
      4. Deterministic session cleanup in finally block.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Worker DB transaction rolled back due to error: {exc}", exc_info=True)
        raise
    finally:
        db.close()
