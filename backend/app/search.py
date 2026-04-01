"""
Hybrid search: semantic vector search + keyword filters.

For text queries:
1. Semantic search via sentence-transformers gives top-50 candidates
2. Apply keyword/filter constraints on those candidates
3. Re-rank by: semantic_score * 0.6 + normalized_karma * 0.4

For filter-only queries (no text):
- Standard SQL filters sorted by karma/etc.

This gives results like:
  "CPO" → finds agents with "product strategy", "roadmap", "product leadership"
  "ML researcher" → finds agents with "PyTorch", "neural networks", "training"
  "automation engineer" → finds agents with "workflow", "pipeline", "cron"
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from typing import Optional
from datetime import datetime, timedelta
import logging

from .models import Agent

logger = logging.getLogger(__name__)


def _json_contains(column, value: str):
    """SQLite-compatible JSON array contains check."""
    return cast(column, String).like(f'%"{value}"%')


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

    # ── Semantic path ───────────────────────────────────────────────────────
    if q:
        try:
            from .embeddings import semantic_search, expand_query, is_ready
            if is_ready():
                expanded = expand_query(q)
                semantic_results = semantic_search(expanded, top_k=200)
                # Build id→score map
                score_map = {agent_id: score for agent_id, score in semantic_results}
                candidate_ids = list(score_map.keys())

                # Get max karma for normalization
                max_karma = db.query(Agent).order_by(Agent.karma.desc()).first()
                max_k = max(1, max_karma.karma if max_karma else 1)

                # Fetch candidates and apply filters
                query = db.query(Agent).filter(Agent.id.in_(candidate_ids))
                query = _apply_filters(query, tag, tech, domain, language, verified,
                                       active_days, min_karma, has_projects, availability)

                all_candidates = query.all()
                total = len(all_candidates)

                # Hybrid re-ranking: semantic + karma boost
                def rank_score(a: Agent) -> float:
                    sem = score_map.get(a.id, 0.0)
                    karma_norm = min(1.0, (a.karma or 0) / max_k)
                    return sem * 0.65 + karma_norm * 0.35

                ranked = sorted(all_candidates, key=rank_score, reverse=True)
                page = ranked[offset:offset + limit]

                from .main import _agent_dict
                return {"total": total, "agents": [_agent_dict(a) for a in page],
                        "offset": offset, "limit": limit, "search_mode": "semantic"}

        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword: {e}")

    # ── Keyword / filter path ───────────────────────────────────────────────
    query = db.query(Agent)

    if q:
        terms = q.lower().split()
        term_filters = []
        for term in terms[:6]:
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
        if term_filters:
            query = query.filter(or_(*term_filters))

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
            "offset": offset, "limit": limit, "search_mode": "keyword"}


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
