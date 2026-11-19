from fastapi import APIRouter
from app.api.deps import CurrentUser, DbSession, owned_paper
from app.models.entities import ChatMessage, ChatSession
from app.schemas import ChatRequest
from app.services.intelligence import answer_question

router = APIRouter(prefix="/api/chat", tags=["Research chat"])


@router.post("/{paper_id}")
def chat(paper_id: int, payload: ChatRequest, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    session = None
    if payload.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == payload.session_id, ChatSession.paper_id == paper.id, ChatSession.user_id == user.id).first()
    if not session:
        session = ChatSession(paper_id=paper.id, user_id=user.id, title=payload.question[:120])
        db.add(session)
        db.flush()
    answer, sources = answer_question(paper, payload.question)
    db.add_all([ChatMessage(session_id=session.id, role="user", content=payload.question), ChatMessage(session_id=session.id, role="assistant", content=answer, sources=sources)])
    db.commit()
    return {"session_id": session.id, "answer": answer, "sources": sources}


@router.get("/{paper_id}/history")
def history(paper_id: int, user: CurrentUser, db: DbSession, session_id: int | None = None):
    owned_paper(paper_id, user, db)
    query = db.query(ChatSession).filter(ChatSession.paper_id == paper_id, ChatSession.user_id == user.id)
    if session_id:
        query = query.filter(ChatSession.id == session_id)
    sessions = query.order_by(ChatSession.created_at.desc()).all()
    return [{"id": session.id, "title": session.title, "messages": [{"id": message.id, "role": message.role, "content": message.content, "sources": message.sources, "created_at": message.created_at} for message in session.messages]} for session in sessions]

