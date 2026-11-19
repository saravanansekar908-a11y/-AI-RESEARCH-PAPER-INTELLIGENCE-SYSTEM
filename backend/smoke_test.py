"""Small end-to-end API verification; run from the backend directory."""
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./smoke_test.db"
os.environ["UPLOADS_DIR"] = "smoke_uploads"

import fitz
from fastapi.testclient import TestClient
from app.main import app


def pdf_bytes(title: str, body: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), f"{title}\n\nAbstract. {body}\n\nMethodology. We use a Transformer model and evaluate it on the Example Dataset.\n\nLimitations. The sample size is limited. Future work should test more domains.")
    result = document.tobytes()
    document.close()
    return result


with TestClient(app) as client:
    register = client.post("/api/auth/register", json={"name": "Test Researcher", "email": "test@example.org", "password": "a-secure-password"})
    assert register.status_code == 201, register.text
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    first = client.post("/api/papers/upload", headers=headers, files={"file": ("first.pdf", pdf_bytes("First paper", "This paper studies reliable retrieval."), "application/pdf")}, data={"topic": "NLP"})
    assert first.status_code == 201, first.text
    second = client.post("/api/papers/upload", headers=headers, files={"file": ("second.pdf", pdf_bytes("Second paper", "This paper studies grounded question answering."), "application/pdf")}, data={"topic": "NLP"})
    assert second.status_code == 201, second.text
    paper_id = first.json()["id"]

    assert client.get("/api/papers", headers=headers).status_code == 200
    summary = client.post(f"/api/analysis/{paper_id}/summary", headers=headers, json={"detail_level": "short"})
    assert summary.status_code == 200, summary.text
    assert "methodology" in summary.json()["content"]
    chat = client.post(f"/api/chat/{paper_id}", headers=headers, json={"question": "What model is used?"})
    assert chat.status_code == 200, chat.text
    assert chat.json()["sources"]
    comparison = client.post("/api/compare", headers=headers, json={"paper_ids": [paper_id, second.json()["id"]]})
    assert comparison.status_code == 200, comparison.text
    dashboard = client.get("/api/dashboard/stats", headers=headers)
    assert dashboard.status_code == 200 and dashboard.json()["total_papers"] == 2, dashboard.text

print("Smoke test passed: auth, upload, analysis, RAG chat, comparison, and dashboard.")

