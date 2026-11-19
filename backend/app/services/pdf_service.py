import re
from pathlib import Path
from uuid import uuid4
import fitz
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.entities import Paper, PaperSection
from app.services.retrieval import embed_text


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunks(text: str, limit: int = 1100) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for sentence in sentences:
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > limit:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def _title_from_text(text: str, fallback: str) -> str:
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 12]
    for line in lines[:12]:
        normalized = line.lower()
        if normalized not in {"abstract", "introduction", "keywords"} and len(line) < 240:
            return line
    return Path(fallback).stem[:500]


def _year_from_text(text: str) -> int | None:
    match = re.search(r"\b(?:19|20)\d{2}\b", text)
    return int(match.group()) if match else None


def _page_text(page) -> str:
    text = page.get_text("text")
    if text.strip():
        return text
    try:
        import pytesseract
        from PIL import Image
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        return pytesseract.image_to_string(image)
    except Exception:
        return ""


async def persist_pdf(upload: UploadFile, user_id: int, db: Session, topic: str | None = None) -> Paper:
    settings = get_settings()
    filename = upload.filename or "paper.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only PDF files are accepted")
    payload = await upload.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(payload) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"PDF must be at most {settings.max_upload_mb} MB")
    if not payload.startswith(b"%PDF"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="The uploaded file is not a valid PDF")

    safe_name = f"{uuid4().hex}.pdf"
    storage_path = settings.upload_path / safe_name
    storage_path.write_bytes(payload)
    paper = Paper(owner_id=user_id, title=Path(filename).stem[:500], filename=filename[:255], storage_path=str(storage_path), file_size=len(payload), topic=topic)
    db.add(paper)
    db.flush()
    try:
        document = fitz.open(stream=payload, filetype="pdf")
        paper.page_count = len(document)
        first_text = ""
        position = 0
        for page_number, page in enumerate(document, start=1):
            text = _page_text(page)
            if page_number <= 2:
                first_text += text
            cleaned = _clean(text)
            for chunk in _chunks(cleaned):
                db.add(PaperSection(paper_id=paper.id, page_number=page_number, position=position, content=chunk, embedding=embed_text(chunk)))
                position += 1
        paper.title = _title_from_text(first_text, filename)
        paper.publication_year = _year_from_text(first_text)
        if position == 0:
            paper.status = "needs_ocr"
            paper.extraction_error = "No text could be extracted. For scanned PDFs, install and configure the Tesseract OCR binary."
        else:
            paper.status = "ready"
        document.close()
    except Exception as exc:
        paper.status = "failed"
        paper.extraction_error = "The PDF could not be processed. Verify the file is not encrypted or corrupt."
        # File remains available to the owner for a later reprocessing attempt.
    db.commit()
    db.refresh(paper)
    return paper

