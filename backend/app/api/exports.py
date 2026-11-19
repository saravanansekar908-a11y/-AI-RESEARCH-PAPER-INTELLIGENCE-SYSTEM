from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.deps import CurrentUser, DbSession, owned_paper
from app.services.intelligence import build_summary

router = APIRouter(prefix="/api/exports", tags=["Exports"])


@router.get("/{paper_id}/summary")
def export_summary(paper_id: int, format: str, user: CurrentUser, db: DbSession):
    paper = owned_paper(paper_id, user, db)
    content = build_summary(paper, "medium")
    if format == "docx":
        from docx import Document
        document = Document()
        document.add_heading(paper.title, 0)
        document.add_paragraph(f"Exported from AI Research Paper Intelligence System • Source: {paper.filename}")
        for heading, text in content.items():
            document.add_heading(heading.replace("_", " ").title(), level=1)
            document.add_paragraph(text)
        output = BytesIO()
        document.save(output)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="paper-{paper.id}-summary.docx"'})
    if format == "pdf":
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        output = BytesIO()
        styles = getSampleStyleSheet()
        flow = [Paragraph(paper.title, styles["Title"]), Spacer(1, 12)]
        for heading, text in content.items():
            flow += [Paragraph(heading.replace("_", " ").title(), styles["Heading2"]), Paragraph(text, styles["BodyText"]), Spacer(1, 8)]
        SimpleDocTemplate(output, pagesize=A4).build(flow)
        output.seek(0)
        return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="paper-{paper.id}-summary.pdf"'})
    raise HTTPException(status_code=422, detail="format must be 'pdf' or 'docx'")

