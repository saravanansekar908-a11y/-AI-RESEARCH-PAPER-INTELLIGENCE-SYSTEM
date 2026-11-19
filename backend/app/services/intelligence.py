import json
import re
from collections import Counter
from app.core.config import get_settings
from app.services.retrieval import retrieve

SUMMARY_FIELDS = {
    "abstract_summary": ("abstract", "summary"),
    "introduction_summary": ("introduction", "background", "motivation"),
    "problem_statement": ("problem", "challenge", "aim"),
    "research_objectives": ("objective", "goal", "we propose", "aim"),
    "methodology": ("method", "methodology", "approach", "framework"),
    "algorithms_used": ("algorithm", "model", "network", "classifier"),
    "dataset_information": ("dataset", "data set", "corpus", "benchmark"),
    "experimental_results": ("result", "accuracy", "performance", "evaluation"),
    "advantages": ("advantage", "benefit", "improve", "outperform"),
    "limitations": ("limitation", "constraint", "however", "challenge"),
    "conclusion": ("conclusion", "conclude", "in summary"),
    "future_scope": ("future work", "future direction", "further work"),
}


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if len(sentence.strip()) > 35]


def _extract_evidence(sections, terms: tuple[str, ...], maximum: int) -> str:
    matched = []
    for section in sections:
        for sentence in _sentences(section.content):
            lower = sentence.lower()
            if any(term in lower for term in terms):
                matched.append(sentence)
                if len(matched) >= maximum:
                    return " ".join(matched)
    return "Not explicitly identified in the extracted paper text."


def _gemini(prompt: str) -> str | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        return getattr(response, "text", None)
    except Exception:
        return None


def build_summary(paper, level: str) -> dict:
    sections = paper.sections
    count = {"short": 1, "medium": 2, "detailed": 4}[level]
    fallback = {field: _extract_evidence(sections, terms, count) for field, terms in SUMMARY_FIELDS.items()}
    context = "\n\n".join(f"[Page {item.page_number}] {item.content}" for item in sections[:30])
    prompt = (
        "Summarize only the supplied paper evidence. Do not invent missing details. "
        "Return a JSON object whose keys are: " + ", ".join(SUMMARY_FIELDS) + ". "
        "For unsupported information use exactly 'Not stated in the supplied paper.'\n\n" + context
    )
    generated = _gemini(prompt)
    if generated:
        try:
            parsed = json.loads(generated.removeprefix("```json").removesuffix("```").strip())
            if all(key in parsed for key in SUMMARY_FIELDS):
                return {key: str(parsed[key]) for key in SUMMARY_FIELDS}
        except (json.JSONDecodeError, AttributeError):
            pass
    return fallback


def methodology(paper) -> dict:
    return {
        "research_problem": _extract_evidence(paper.sections, ("problem", "challenge", "aim"), 3),
        "proposed_methodology": _extract_evidence(paper.sections, ("method", "approach", "propose"), 4),
        "algorithms": _extract_evidence(paper.sections, ("algorithm", "model", "network"), 3),
        "model_architecture": _extract_evidence(paper.sections, ("architecture", "layer", "encoder", "decoder"), 3),
        "dataset": _extract_evidence(paper.sections, ("dataset", "data set", "corpus", "benchmark"), 3),
        "evaluation_metrics": _extract_evidence(paper.sections, ("metric", "accuracy", "f1", "precision", "recall"), 3),
        "experimental_setup": _extract_evidence(paper.sections, ("experiment", "training", "test set", "validation"), 3),
        "results": _extract_evidence(paper.sections, ("result", "accuracy", "outperform", "performance"), 3),
    }


def gaps(paper) -> dict:
    stated = _extract_evidence(paper.sections, ("limitation", "limited", "future work", "future direction", "constraint"), 6)
    return {
        "paper_stated_limitations": stated,
        "ai_generated_hypotheses": [],
        "notice": "No AI-generated gap hypotheses are shown without a configured LLM provider. Paper-stated evidence is kept separate from hypotheses.",
    }


def answer_question(paper, question: str) -> tuple[str, list[dict]]:
    selected = retrieve(paper.sections, question)
    sources = [{"page": item.page_number, "excerpt": item.content[:500]} for item in selected]
    if not selected:
        return "No extracted text is available for this paper. It may require OCR before it can be queried.", sources
    context = "\n\n".join(f"[Page {item.page_number}] {item.content}" for item in selected)
    prompt = (
        "Answer the question using only the supplied paper excerpts. Cite pages as [p. N]. "
        "If the evidence does not answer it, say it is not available in the paper.\n\n"
        f"Question: {question}\n\nEvidence:\n{context}"
    )
    generated = _gemini(prompt)
    if generated:
        return generated, sources
    evidence = " ".join(item.content[:350] for item in selected[:2])
    return f"An LLM provider is not configured, so here is the most relevant evidence from the paper: {evidence}", sources


def topic_counts(papers) -> list[dict]:
    counts = Counter((paper.topic or "Uncategorized") for paper in papers)
    return [{"name": key, "value": value} for key, value in counts.most_common()]

