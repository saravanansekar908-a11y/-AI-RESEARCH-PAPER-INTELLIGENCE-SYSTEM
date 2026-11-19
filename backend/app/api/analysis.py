from fastapi import APIRouter
from app.api.deps import CurrentUser, DbSession, owned_paper
from app.models.entities import PaperSummary, ResearchAnalysis
from app.schemas import SummaryRequest
from app.services.intelligence import build_summary, gaps, methodology

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/{paper_id}/summary")
def summary(paper_id: int, payload: SummaryRequest, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    content = build_summary(paper, payload.detail_level)
    saved = PaperSummary(paper_id=paper.id, detail_level=payload.detail_level, content=content)
    db.add(saved)
    db.commit()
    return {"paper_id": paper.id, "detail_level": payload.detail_level, "content": content}


@router.post("/{paper_id}/methodology")
def extract_methodology(paper_id: int, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    content = methodology(paper)
    db.add(ResearchAnalysis(paper_id=paper.id, analysis_type="methodology", content=content))
    db.commit()
    return {"paper_id": paper.id, "content": content}


@router.post("/{paper_id}/research-gaps")
def research_gaps(paper_id: int, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    content = gaps(paper)
    db.add(ResearchAnalysis(paper_id=paper.id, analysis_type="research_gaps", content=content))
    db.commit()
    return {"paper_id": paper.id, "content": content}

