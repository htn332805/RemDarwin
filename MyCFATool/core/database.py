from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from .config import config


class DatabaseSessionManager:
    """Manages SQLAlchemy database sessions."""

    def __init__(self):
        db_url = config.get_database_url()
        db_config = config.config.get('database', {})

        # Configure connection pooling for PostgreSQL production
        pool_config = db_config.get('connection_pool', {})
        if 'postgresql' in db_url:
            self.engine = create_engine(
                db_url,
                echo=False,
                pool_size=pool_config.get('min', 5),
                max_overflow=pool_config.get('max', 20) - pool_config.get('min', 5),  # max - min
                pool_timeout=pool_config.get('timeout', 30),
                pool_recycle=3600,  # Recycle connections every hour
                pool_pre_ping=True  # Test connections before use
            )
        else:
            # SQLite doesn't support pooling
            self.engine = create_engine(db_url, echo=False)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Singleton instance
db_manager = DatabaseSessionManager()

# Convenience function for getting a session
def get_session():
    return db_manager.session()