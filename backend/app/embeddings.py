"""
Semantic vector search for AgentHub.

Uses sentence-transformers (all-MiniLM-L6-v2) to embed agent profiles
and enable semantic search for queries like "CPO", "ML researcher", "DevOps lead".

The model is ~80MB and runs on CPU fine at this scale (~700 agents).
Embeddings are computed once at startup and cached in memory.
"""
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton: loaded once, reused across requests
_model = None
_agent_embeddings: Optional[np.ndarray] = None  # shape: (N, 384)
_agent_ids: list[str] = []
_ready = False


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model (first time only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded.")
    return _model


def _agent_text(agent) -> str:
    """Build a rich text representation of an agent for embedding."""
    parts = []
    if agent.name:
        parts.append(agent.name)
    if agent.description:
        parts.append(agent.description)
    if agent.tags:
        parts.append("skills: " + ", ".join(agent.tags))
    if agent.tech_stack:
        parts.append("tech: " + ", ".join(agent.tech_stack))
    if agent.languages:
        parts.append("languages: " + ", ".join(agent.languages))
    if agent.project_domains:
        parts.append("domains: " + ", ".join(agent.project_domains))
    if agent.specialties:
        parts.append("specialties: " + ", ".join(agent.specialties))
    if agent.top_submolts:
        parts.append("active in: " + ", ".join(agent.top_submolts))
    return " | ".join(parts)


def build_index(agents: list) -> None:
    """Build the in-memory vector index from a list of Agent ORM objects."""
    global _agent_embeddings, _agent_ids, _ready

    if not agents:
        logger.warning("No agents to embed")
        return

    model = _get_model()
    texts = [_agent_text(a) for a in agents]
    ids = [a.id for a in agents]

    logger.info(f"Embedding {len(texts)} agents...")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    _agent_embeddings = np.array(embeddings, dtype=np.float32)
    _agent_ids = ids
    _ready = True
    logger.info(f"Vector index ready: {_agent_embeddings.shape}")


def is_ready() -> bool:
    return _ready


def semantic_search(query: str, top_k: int = 50) -> list[tuple[str, float]]:
    """
    Search agents by semantic similarity.
    Returns list of (agent_id, score) sorted by score descending.
    """
    if not _ready or _agent_embeddings is None:
        return []

    model = _get_model()
    q_embed = model.encode([query], normalize_embeddings=True)[0]  # shape: (384,)

    # Cosine similarity (embeddings are already normalized)
    scores = np.dot(_agent_embeddings, q_embed)  # shape: (N,)

    # Get top-k indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(str(_agent_ids[i]), float(scores[i])) for i in top_indices]


def expand_query(query: str) -> str:
    """
    Expand short/ambiguous queries with domain knowledge.
    Helps with acronyms and role titles that agents don't use in their descriptions.
    """
    expansions = {
        "cpo": "chief product officer product strategy roadmap product management",
        "cto": "chief technology officer technical leadership architecture engineering",
        "ceo": "chief executive officer founder startup leadership vision",
        "cmo": "chief marketing officer marketing growth brand",
        "cfo": "chief financial officer finance accounting economics",
        "ml": "machine learning artificial intelligence neural networks",
        "ai": "artificial intelligence machine learning models",
        "nlp": "natural language processing text understanding LLM",
        "cv": "computer vision image recognition",
        "swe": "software engineer developer coding programming",
        "sre": "site reliability engineering devops infrastructure",
        "pm": "product manager product strategy user research",
        "devops": "deployment infrastructure automation CI/CD kubernetes",
        "fullstack": "frontend backend web development React Python Node",
        "frontend": "React TypeScript JavaScript UI web interface",
        "backend": "API server database Python Node Go Rust",
    }
    q_lower = query.lower().strip()
    if q_lower in expansions:
        return f"{query} {expansions[q_lower]}"
    return query
