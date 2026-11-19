from collections import Counter
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, DbSession
from app.models.entities import Paper, PaperComparison, PaperSummary, ResearchAnalysis, LiteratureReview
from app.schemas import CompareRequest, LiteratureRequest
from app.services.intelligence import build_summary, methodology, topic_counts

router = APIRouter(prefix="/api", tags=["Research intelligence"])


def _papers_for_user(paper_ids: list[int], user_id: int, db: DbSession) -> list[Paper]:
    papers = db.query(Paper).filter(Paper.id.in_(paper_ids), Paper.owner_id == user_id).all()
    if len(papers) != len(set(paper_ids)):
        raise HTTPException(status_code=404, detail="One or more selected papers were not found")
    return papers


@router.post("/compare")
def compare(payload: CompareRequest, user: CurrentUser, db: DbSession):
    papers = _papers_for_user(payload.paper_ids, user.id, db)
    rows = []
    for paper in papers:
        data = methodology(paper)
        rows.append({
            "paper_id": paper.id, "paper": paper.title, "research_objective": build_summary(paper, "short")["research_objectives"],
            "methodology": data["proposed_methodology"], "algorithms": data["algorithms"], "dataset": data["dataset"],
            "evaluation_metrics": data["evaluation_metrics"], "results": data["results"],
            "limitations": build_summary(paper, "short")["limitations"], "future_directions": build_summary(paper, "short")["future_scope"],
        })
    content = {"rows": rows}
    db.add(PaperComparison(user_id=user.id, paper_ids=payload.paper_ids, content=content))
    db.commit()
    return content


@router.post("/literature-review/generate")
def literature_review(payload: LiteratureRequest, user: CurrentUser, db: DbSession):
    papers = _papers_for_user(payload.paper_ids, user.id, db)
    sections = [f"# {payload.title}", "## Included papers"]
    for paper in papers:
        summary = build_summary(paper, "short")
        sections.extend([
            f"### {paper.title}",
            f"**Source file:** {paper.filename}",
            f"**Objective evidence:** {summary['research_objectives']}",
            f"**Method evidence:** {summary['methodology']}",
            f"**Result evidence:** {summary['experimental_results']}",
        ])
    sections.append("## Notes\nThis draft only organizes evidence from uploaded papers. It does not invent bibliographic citations.")
    content = "\n\n".join(sections)
    record = LiteratureReview(user_id=user.id, paper_ids=payload.paper_ids, title=payload.title, content=content)
    db.add(record)
    db.commit()
    return {"id": record.id, "title": record.title, "content": record.content}


@router.get("/dashboard/stats")
def dashboard_stats(user: CurrentUser, db: DbSession):
    papers = db.query(Paper).filter(Paper.owner_id == user.id).order_by(Paper.created_at.desc()).all()
    paper_ids = [paper.id for paper in papers]
    summary_count = db.query(PaperSummary).filter(PaperSummary.paper_id.in_(paper_ids)).count() if paper_ids else 0
    analysis_count = db.query(ResearchAnalysis).filter(ResearchAnalysis.paper_id.in_(paper_ids)).count() if paper_ids else 0
    return {
        "total_papers": len(papers), "papers_analyzed": len({item.paper_id for item in db.query(PaperSummary).filter(PaperSummary.paper_id.in_(paper_ids)).all()}) if paper_ids else 0,
        "analysis_runs": summary_count + analysis_count,
        "recent_papers": [{"id": paper.id, "title": paper.title, "topic": paper.topic, "status": paper.status, "created_at": paper.created_at} for paper in papers[:5]],
    }


@router.get("/analytics/research-trends")
def research_trends(user: CurrentUser, db: DbSession):
    papers = db.query(Paper).filter(Paper.owner_id == user.id).all()
    algorithms = Counter()
    datasets = Counter()
    for paper in papers:
        text = " ".join(section.content.lower() for section in paper.sections)
        for name in ("transformer", "bert", "cnn", "rnn", "svm", "random forest", "xgboost", "lstm"):
            if name in text:
                algorithms[name.upper() if name == "bert" else name.title()] += 1
        for match in __import__("re").findall(r"(?:[A-Z][\w-]+\s+){0,2}(?:dataset|corpus|benchmark)", " ".join(section.content for section in paper.sections)):
            datasets[match.strip()] += 1
    years = Counter(str(paper.publication_year) for paper in papers if paper.publication_year)
    return {
        "publication_years": [{"name": name, "value": value} for name, value in sorted(years.items())],
        "topics": topic_counts(papers),
        "algorithms": [{"name": name, "value": value} for name, value in algorithms.most_common()],
        "datasets": [{"name": name, "value": value} for name, value in datasets.most_common(12)],
    }

