import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Default to a local Postgres if not provided
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://rag_user:rag_pass@localhost:5432/ragdb",
)

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=True)
    authors = Column(String(1024), nullable=True)
    year = Column(String(8), nullable=True)
    filename = Column(String(512), nullable=False)
    pages = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def save_paper_meta(*, title: Optional[str], authors: Optional[str], year: Optional[str], filename: str, pages: Optional[int]) -> int:
    """Persist basic paper metadata and return the DB id."""
    with SessionLocal() as session:
        paper = Paper(title=title, authors=authors, year=year, filename=filename, pages=pages)
        session.add(paper)
        session.commit()
        session.refresh(paper)
        return paper.id
