import json
import re
from collections import Counter
from app.core.config import get_settings
from app.services.retrieval import query_terms, retrieve, tokenize

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
    sentences = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence = re.sub(r"^[\s\u2022\ufffd�\-]+", "", sentence).strip()
        if len(sentence) > 35:
            sentences.append(sentence)
    return sentences


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
    if not paper.sections:
        return "I couldn’t find extracted text for this paper. It may need OCR before I can answer questions about it.", []

    question_tokens = set(tokenize(question))
    generic = {"paper", "study", "use", "used", "using", "introduce", "introduced", "describe", "explain", "tell", "about", "include", "including", "find", "give", "state", "many", "much", "number"}
    intent_terms = {
        "architecture": {"architecture", "transformer", "encoder", "decoder", "attention"},
        "layer": {"layer", "layers", "encoder", "decoder", "stacked", "number"},
        "model": {"model", "models", "transformer", "bert", "cnn", "rnn", "svm", "network", "encoder"},
        "algorithm": {"algorithm", "transformer", "bert", "cnn", "rnn", "svm", "network"},
        "dataset": {"dataset", "corpus", "benchmark", "wmt", "data"},
        "result": {"result", "accuracy", "performance", "bleu", "f1", "improve"},
        "limitation": {"limitation", "limited", "constraint", "future", "challenge"},
        "problem": {"problem", "challenge", "issue", "solve", "addresses"},
    }
    expected = set().union(*(terms for intent, terms in intent_terms.items() if intent in question_tokens))
    requested = (question_tokens - generic) | expected
    if not requested:
        return "I couldn’t find a passage in this paper that answers that question. Try asking about a specific topic, method, result, or limitation.", []

    # Score and select at sentence level. Chunk-level retrieval can surface a
    # page that contains a stray query word (for example a copyright footer).
    evidence = []
    for section in paper.sections:
        for sentence in _sentences(section.content):
            if len(sentence) > 420 or re.search(r"feature\s+existing system\s+proposed system|table\s+\d+\.\d+", sentence, re.I):
                continue
            sentence_tokens = set(tokenize(sentence))
            matched = requested.intersection(sentence_tokens)
            intent_matched = expected.intersection(sentence_tokens)
            if not matched:
                continue
            score = len(matched) + 2 * len(intent_matched)
            evidence.append((score, len(intent_matched), section.page_number, sentence, sentence_tokens))

    evidence.sort(key=lambda item: (item[0], item[1], -item[2]), reverse=True)
    if not evidence:
        return "I couldn’t find a passage in this paper that answers that question. Try asking about a specific topic, method, result, or limitation.", []

    top_score = evidence[0][0]
    # Reject weak matches: require either an intent match or two content words.
    qualifying = [item for item in evidence if item[0] >= max(2, top_score - 1) and (item[1] > 0 or len(requested.intersection(item[4])) >= 2)]
    if not qualifying:
        return "I couldn’t find a passage in this paper that answers that question. Try asking about a specific topic, method, result, or limitation.", []

    # Count questions require explicit numeric evidence; a sentence that only
    # says "stacked layers" cannot support an exact layer count.
    if re.search(r"\bhow many\b|\bnumber of\b|\bhow much\b", question, re.I):
        numeric = [item for item in qualifying if re.search(r"\b\d+(?:\.\d+)?\b|\b(one|two|three|four|five|six|seven|eight|nine|ten|dozen|hundred|thousand)\b", item[3], re.I)]
        if not numeric:
            return "The paper discusses this, but I couldn’t find an explicit count in the extracted text.", []
        qualifying = numeric

    chosen = []
    seen = set()
    for _, _, page, sentence, _ in qualifying:
        normalized = sentence.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        chosen.append((page, sentence))
        if len(chosen) == 2:
            break
    sources = [{"page": page, "excerpt": sentence[:500]} for page, sentence in chosen]
    if not sources:
        return "I couldn’t find a passage in this paper that answers that question. Try rephrasing it with terms used in the paper.", []

    context = "\n\n".join(f"[Page {page}] {sentence}" for page, sentence in chosen)
    prompt = (
        "Answer the question using only the supplied paper excerpts. Give a concise direct answer. "
        "Cite every factual claim with the supporting page as [p. N]. Do not use general knowledge. "
        "If the evidence does not answer it, say it is not available in the paper.\n\n"
        f"Question: {question}\n\nEvidence:\n{context}"
    )
    generated = _gemini(prompt)
    if generated:
        return generated.strip(), sources

    answer_parts = []
    for page, sentence in chosen:
        citation = f"[p. {page}]"
        if answer_parts and citation in answer_parts[-1]:
            continue
        answer_parts.append(f"{sentence} {citation}")
    return " ".join(answer_parts), sources


def topic_counts(papers) -> list[dict]:
    counts = Counter((paper.topic or "Uncategorized") for paper in papers)
    return [{"name": key, "value": value} for key, value in counts.most_common()]

