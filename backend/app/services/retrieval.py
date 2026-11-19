import hashlib
import math
import re
from functools import lru_cache
from app.core.config import get_settings


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
    query_vector = embed_text(query)
    ranked = sorted(sections, key=lambda item: cosine(query_vector, item.embedding or []), reverse=True)
    return ranked[:limit]

