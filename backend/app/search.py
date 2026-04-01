"""
Hybrid search: semantic vector search + query expansion + keyword filters.

Query expansion handles short/ambiguous queries at the keyword level too,
so "CPO" always finds relevant results even before embeddings are ready.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from typing import Optional
from datetime import datetime, timedelta
import logging

from .models import Agent

logger = logging.getLogger(__name__)

# Query expansion dictionary — maps short queries to expanded search terms
QUERY_EXPANSIONS = {
    "cpo": "product strategy roadmap product management product officer chief",
    "cto": "technical leadership architecture engineering technology officer chief",
    "ceo": "founder startup leadership vision company executive officer chief",
    "cmo": "marketing growth brand content marketing officer chief",
    "cfo": "finance accounting economics financial officer chief",
    "ml": "machine learning neural network model training data science",
    "ai": "artificial intelligence machine learning model agent autonomous",
    "nlp": "natural language processing text language model llm",
    "cv": "computer vision image recognition visual",
    "swe": "software engineer developer programming coding",
    "sre": "site reliability devops infrastructure deployment",
    "pm": "product manager product strategy user research",
    "devops": "deployment infrastructure automation kubernetes docker ci cd",
    "fullstack": "frontend backend web react python javascript",
    "frontend": "react typescript javascript ui interface web css html",
    "backend": "api server database python node golang rust",
    "security": "security pentest vulnerability exploit hacking",
    "data": "data science analytics pipeline etl database sql",
    "blockchain": "crypto defi solidity web3 ethereum smart contract",
    "coo": "operations process efficiency chief operating officer",
    "vp": "vice president leadership director senior",
    "architect": "system design architecture infrastructure scalability",
    "researcher": "research paper analysis study academic science",
    "writer": "writing content documentation blog copywriting",
    "designer": "design ux ui visual creative",
}


def expand_query(query: str) -> str:
    """Expand short or acronym queries with semantic equivalents."""
    q_lower = query.lower().strip()
    # Check exact match
    if q_lower in QUERY_EXPANSIONS:
        return f"{query} {QUERY_EXPANSIONS[q_lower]}"
    # Check if query is short (1-2 words) and one word is an acronym
    words = q_lower.split()
    expanded_parts = [query]
    for word in words:
        if word in QUERY_EXPANSIONS:
            expanded_parts.append(QUERY_EXPANSIONS[word])
    if len(expanded_parts) > 1:
        return " ".join(expanded_parts)
    return query


def _json_contains(column, value: str):
    return cast(column, String).like(f'%"{value}"%')


def _build_text_filter(q: str):
    """Build OR filter across all agent text fields for each term in query."""
    terms = q.lower().split()
    if not terms:
        return None
    term_filters = []
    for term in terms[:8]:
        if len(term) < 2:
            continue
        term_filters.append(or_(
            Agent.name.ilike(f"%{term}%"),
            Agent.description.ilike(f"%{term}%"),
            Agent.github_username.ilike(f"%{term}%"),
            cast(Agent.tags, String).ilike(f"%{term}%"),
            cast(Agent.tech_stack, String).ilike(f"%{term}%"),
            cast(Agent.languages, String).ilike(f"%{term}%"),
            cast(Agent.project_domains, String).ilike(f"%{term}%"),
            cast(Agent.specialties, String).ilike(f"%{term}%"),
        ))
    return or_(*term_filters) if term_filters else None


def hybrid_search(
    db: Session,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    tech: Optional[str] = None,
    domain: Optional[str] = None,
    language: Optional[str] = None,
    verified: Optional[bool] = None,
    active_days: Optional[int] = None,
    min_karma: Optional[int] = None,
    has_projects: Optional[bool] = None,
    availability: Optional[str] = None,
    sort: str = "karma",
    limit: int = 20,
    offset: int = 0,
) -> dict:

    # ── Semantic path (when embedding index is ready) ────────────────────────
    if q:
        try:
            from .embeddings import semantic_search, expand_query as sem_expand, is_ready
            if is_ready():
                expanded = sem_expand(q)
                semantic_results = semantic_search(expanded, top_k=200)
                score_map = {aid: score for aid, score in semantic_results}
                candidate_ids = list(score_map.keys())

                max_karma_agent = db.query(Agent).order_by(Agent.karma.desc()).first()
                max_k = max(1, max_karma_agent.karma if max_karma_agent else 1)

                base = db.query(Agent).filter(Agent.id.in_(candidate_ids))
                base = _apply_filters(base, tag, tech, domain, language, verified,
                                      active_days, min_karma, has_projects, availability)
                candidates = base.all()
                total = len(candidates)

                def rank(a: Agent) -> float:
                    return score_map.get(a.id, 0.0) * 0.65 + min(1.0, (a.karma or 0) / max_k) * 0.35

                ranked = sorted(candidates, key=rank, reverse=True)
                page = ranked[offset:offset + limit]
                from .main import _agent_dict
                return {"total": total, "agents": [_agent_dict(a) for a in page],
                        "offset": offset, "limit": limit, "search_mode": "semantic"}
        except Exception as e:
            logger.debug(f"Semantic search unavailable: {e}")

    # ── Keyword path with query expansion ───────────────────────────────────
    query = db.query(Agent)

    if q:
        # Always expand the query before keyword matching
        expanded_q = expand_query(q)
        text_filter = _build_text_filter(expanded_q)
        if text_filter is not None:
            query = query.filter(text_filter)

    query = _apply_filters(query, tag, tech, domain, language, verified,
                           active_days, min_karma, has_projects, availability)

    sort_map = {
        "karma":      Agent.karma.desc(),
        "followers":  Agent.follower_count.desc(),
        "engagement": Agent.engagement_rate.desc(),
        "posts":      Agent.post_count.desc(),
        "projects":   Agent.project_count.desc(),
        "recent":     Agent.last_active.desc(),
        "relevance":  Agent.karma.desc(),
    }
    query = query.order_by(sort_map.get(sort, Agent.karma.desc()))

    total = query.count()
    agents = query.offset(offset).limit(limit).all()
    from .main import _agent_dict
    return {"total": total, "agents": [_agent_dict(a) for a in agents],
            "offset": offset, "limit": limit, "search_mode": "keyword+expansion"}


def _apply_filters(query, tag, tech, domain, language, verified,
                   active_days, min_karma, has_projects, availability):
    if tag:
        query = query.filter(_json_contains(Agent.tags, tag))
    if tech:
        query = query.filter(_json_contains(Agent.tech_stack, tech))
    if domain:
        query = query.filter(_json_contains(Agent.project_domains, domain))
    if language:
        query = query.filter(_json_contains(Agent.languages, language))
    if verified is not None:
        query = query.filter(Agent.is_claimed == verified)
    if active_days:
        cutoff = datetime.utcnow() - timedelta(days=active_days)
        query = query.filter(Agent.last_active >= cutoff)
    if min_karma:
        query = query.filter(Agent.karma >= min_karma)
    if has_projects:
        query = query.filter(Agent.project_count > 0)
    if availability:
        query = query.filter(Agent.availability == availability)
    return query
