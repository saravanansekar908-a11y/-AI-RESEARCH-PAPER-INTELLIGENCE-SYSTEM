import hashlib
import math
import re
from functools import lru_cache
from app.core.config import get_settings

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "does", "for", "from", "how", "in", "is", "it",
    "of", "on", "or", "that", "the", "their", "this", "to", "was", "what", "which", "who", "why", "with",
}

TOKEN_VARIANTS = {
    "use": {"use", "used", "using"},
    "introduce": {"introduce", "introduced", "introduces"},
    "layer": {"layer", "layers"},
    "model": {"model", "models"},
    "result": {"result", "results"},
    "dataset": {"dataset", "datasets"},
}

INTENT_TERMS = {
    "problem": {"problem", "challenge", "issue", "difficulty", "addresses", "solve", "solves", "manual", "scattered", "fragmented"},
    "solve": {"problem", "challenge", "issue", "addresses", "solve", "solves", "solution", "overcome"},
    "objective": {"objective", "objectives", "aim", "goal", "purpose", "designed", "develop"},
    "method": {"method", "methodology", "approach", "proposed", "system", "framework", "architecture"},
    "algorithm": {"algorithm", "model", "network", "classifier", "transformer", "method"},
    "dataset": {"dataset", "data", "corpus", "benchmark", "sample"},
    "result": {"result", "results", "finding", "findings", "outcome", "performance", "evaluation"},
    "limitation": {"limitation", "limitations", "constraint", "weakness", "future", "challenge", "recommendation", "recommendations", "improvement", "improvements", "enhancement", "enhancements"},
    "improvement": {"improvement", "improvements", "recommendation", "recommendations", "enhancement", "enhancements", "future", "suggested", "proposed"},
    "recommendation": {"recommendation", "recommendations", "improvement", "improvements", "enhancement", "enhancements", "future", "suggested"},
}


def tokenize(text: str) -> list[str]:
    tokens = []
    for token in re.findall(r"[a-z0-9]{2,}", text.lower()):
        if token in STOP_WORDS:
            continue
        if len(token) > 5 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        tokens.append(token)
    return tokens


def query_terms(query: str) -> set[str]:
    terms = set(tokenize(query))
    expanded = set(terms)
    for term in terms:
        for base, variants in TOKEN_VARIANTS.items():
            if term == base or term in variants:
                expanded.update(tokenize(" ".join(variants)))
        for synonym in INTENT_TERMS.get(term, ()):
            expanded.update(tokenize(synonym))
    return expanded


def _hash_embedding(text: str, dimension: int = 256) -> list[float]:
    values = [0.0] * dimension
    for token in re.findall(r"[a-z0-9]{2,}", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:2], "big") % dimension
        values[index] += -1.0 if digest[2] % 2 else 1.0
    magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
    return [round(value / magnitude, 6) for value in values]


@lru_cache(maxsize=1)
def _model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(get_settings().embedding_model)
    except Exception:
        return None


def embed_text(text: str) -> list[float]:
    model = _model()
    if model is not None:
        try:
            return model.encode(text, normalize_embeddings=True).tolist()
        except Exception:
            pass
    return _hash_embedding(text)


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def retrieve(sections, query: str, limit: int = 5):
    """Hybrid retrieval: prioritize query terms and intent, with embeddings as a tie-breaker.

    The lexical score remains useful offline and prevents a mismatched or weak
    fallback embedding from outranking a section that directly answers the query.
    """
    if not sections:
        return []

    terms = query_terms(query)
    if not terms:
        return []
    document_tokens = [tokenize(section.content) for section in sections]
    document_frequency = {term: sum(term in tokens for tokens in document_tokens) for term in terms}
    average_length = sum(map(len, document_tokens)) / max(1, len(document_tokens))
    lexical_scores = []
    for tokens in document_tokens:
        frequencies = {}
        for token in tokens:
            frequencies[token] = frequencies.get(token, 0) + 1
        score = 0.0
        for term in terms:
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (len(sections) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            length_normalizer = 1.2 * (0.25 + 0.75 * len(tokens) / max(1.0, average_length))
            score += inverse_frequency * (frequency * 2.2) / (frequency + length_normalizer)
        lexical_scores.append(score)

    query_vector = embed_text(query)
    scored = []
    for index, section in enumerate(sections):
        lexical = lexical_scores[index]
        if lexical <= 0:
            continue
        stored = section.embedding or []
        semantic = max(0.0, cosine(query_vector, stored)) if len(query_vector) == len(stored) else 0.0
        # BM25 is the primary signal; semantic similarity only breaks close matches.
        scored.append((lexical + semantic * 0.12, section))

    scored.sort(key=lambda pair: (pair[0], -pair[1].page_number), reverse=True)
    return [section for _, section in scored[:limit]]

