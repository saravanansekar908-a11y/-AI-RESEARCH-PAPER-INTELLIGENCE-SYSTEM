from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Timestamped, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    papers: Mapped[list["Paper"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Paper(Timestamped, Base):
    __tablename__ = "papers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[str | None] = mapped_column(String(1000))
    publication_year: Mapped[int | None] = mapped_column(Integer)
    topic: Mapped[str | None] = mapped_column(String(255), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="processing", nullable=False)
    extraction_error: Mapped[str | None] = mapped_column(Text)
    owner: Mapped["User"] = relationship(back_populates="papers")
    sections: Mapped[list["PaperSection"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    summaries: Mapped[list["PaperSummary"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    analyses: Mapped[list["ResearchAnalysis"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class PaperSection(Timestamped, Base):
    __tablename__ = "paper_sections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON)
    paper: Mapped["Paper"] = relationship(back_populates="sections")


class PaperSummary(Timestamped, Base):
    __tablename__ = "paper_summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True, nullable=False)
    detail_level: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    paper: Mapped["Paper"] = relationship(back_populates="summaries")


class ChatSession(Timestamped, Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="Research conversation", nullable=False)
    paper: Mapped["Paper"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Timestamped, Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSON)
    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class ResearchAnalysis(Timestamped, Base):
    __tablename__ = "research_analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True, nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    paper: Mapped["Paper"] = relationship(back_populates="analyses")


class PaperComparison(Timestamped, Base):
    __tablename__ = "paper_comparisons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    paper_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)


class LiteratureReview(Timestamped, Base):
    __tablename__ = "literature_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    paper_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

