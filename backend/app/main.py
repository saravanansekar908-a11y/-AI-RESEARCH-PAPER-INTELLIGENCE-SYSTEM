import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api import analysis, auth, chat, exports, papers, research
from app.core.config import get_settings
from app.database import Base, engine
import app.models.entities  # noqa: F401 - imports model metadata

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title=settings.app_name, version="1.0.0", description="Private, grounded research-paper analysis APIs.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    settings.upload_path
    Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request data", "errors": exc.errors()})


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(auth.router)
app.include_router(papers.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(research.router)
app.include_router(exports.router)

# When a production Vite build is present, serve the SPA from the same origin as
# the API. This keeps authenticated API calls simple for local and single-host use.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

