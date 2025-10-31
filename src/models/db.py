import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


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


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(2000), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    confidence = Column(String(16), nullable=True)  # store as string for simplicity, e.g., "0.85"
    rating = Column(Integer, nullable=True)  # optional user satisfaction rating 1-5
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    papers = relationship("QueryPaper", back_populates="query", cascade="all, delete-orphan")


class QueryPaper(Base):
    __tablename__ = "query_papers"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True)

    query = relationship("Query", back_populates="papers")


def init_db():
    Base.metadata.create_all(bind=engine)


def check_paper_exists(filename: str) -> Optional[int]:
    """Check if a paper with the given filename already exists. Returns paper_id if exists, None otherwise."""
    with SessionLocal() as session:
        paper = session.query(Paper).filter(Paper.filename == filename).first()
        return paper.id if paper else None


def save_paper_meta(*, title: Optional[str], authors: Optional[str], year: Optional[str], filename: str, pages: Optional[int]) -> int:
    """Persist basic paper metadata and return the DB id."""
    with SessionLocal() as session:
        paper = Paper(title=title, authors=authors, year=year, filename=filename, pages=pages)
        session.add(paper)
        session.commit()
        session.refresh(paper)
        return paper.id


def save_query_history(*, question: str, paper_ids: Optional[list[int]], response_time_ms: Optional[int], confidence: Optional[float], rating: Optional[int] = None) -> int:
    """Persist a query record with referenced papers. Returns the query id."""
    with SessionLocal() as session:
        q = Query(
            question=question,
            response_time_ms=response_time_ms,
            confidence=f"{confidence:.2f}" if confidence is not None else None,
            rating=rating,
        )
        session.add(q)
        session.flush()  # get q.id

        if paper_ids:
            for pid in paper_ids:
                session.add(QueryPaper(query_id=q.id, paper_id=pid))

        session.commit()
        return q.id


def list_recent_queries(limit: int = 20) -> list[dict]:
    """Return recent queries with basic info and referenced paper IDs."""
    with SessionLocal() as session:
        rows = (
            session.query(Query)
            .order_by(Query.created_at.desc())
            .limit(limit)
            .all()
        )
        results: list[dict] = []
        for r in rows:
            paper_ids = [qp.paper_id for qp in r.papers if qp.paper_id is not None]
            results.append({
                "id": r.id,
                "question": r.question,
                "paper_ids": paper_ids,
                "response_time_ms": r.response_time_ms,
                "confidence": float(r.confidence) if r.confidence is not None else None,
                "rating": r.rating,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return results


def get_popular_topics(limit: int = 10) -> list[dict]:
    """Compute naive 'popular topics' from recent queries by simple keyword frequency."""
    import re
    from collections import Counter

    stop = set(
        "the a an and or of to in on for with from is are was were be been being this that those these what which who why how into across between by as using use method methods methodology results discussion conclusion abstract paper model models algorithm algorithms study studies research".split()
    )
    words: list[str] = []
    recent = list_recent_queries(limit=200)
    for item in recent:
        q = (item.get("question") or "").lower()
        q = re.sub(r"[^a-z0-9\s]", " ", q)
        for w in q.split():
            if len(w) < 3:
                continue
            if w in stop:
                continue
            words.append(w)

    counter = Counter(words)
    top = counter.most_common(limit)
    return [{"topic": k, "count": v} for k, v in top]
