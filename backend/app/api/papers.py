from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import joinedload
from app.api.deps import CurrentUser, DbSession, owned_paper
from app.models.entities import Paper
from app.schemas import PaperOut
from app.services.pdf_service import persist_pdf

router = APIRouter(prefix="/api/papers", tags=["Papers"])


@router.post("/upload", response_model=PaperOut, status_code=status.HTTP_201_CREATED)
async def upload_paper(user: CurrentUser, db: DbSession, file: UploadFile = File(...), topic: str | None = Form(None)):
    return await persist_pdf(file, user.id, db, topic.strip()[:255] if topic else None)


@router.get("", response_model=list[PaperOut])
def list_papers(user: CurrentUser, db: DbSession, search: str | None = None, topic: str | None = None):
    query = db.query(Paper).filter(Paper.owner_id == user.id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(Paper.title.ilike(term))
    if topic:
        query = query.filter(Paper.topic == topic)
    return query.order_by(Paper.created_at.desc()).all()


@router.get("/{paper_id}")
def get_paper(paper_id: int, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    return {
        "id": paper.id, "title": paper.title, "authors": paper.authors, "publication_year": paper.publication_year,
        "topic": paper.topic, "filename": paper.filename, "file_size": paper.file_size, "page_count": paper.page_count,
        "status": paper.status, "extraction_error": paper.extraction_error, "created_at": paper.created_at,
        "sections": [{"page_number": section.page_number, "content": section.content} for section in paper.sections],
    }


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(paper_id: int, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    storage = Path(paper.storage_path)
    db.delete(paper)
    db.commit()
    try:
        if storage.exists():
            storage.unlink()
    except OSError:
        pass

