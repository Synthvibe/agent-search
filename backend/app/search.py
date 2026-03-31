"""
Hybrid search for AgentHub.

Strategy:
- Single terms: filter to agents that contain the term anywhere
- Multi-word queries: use OR across terms (any match), ranked by karma
- Exact tag/tech/language/domain filters: precise JSON array matching
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, cast, String
from typing import Optional
from datetime import datetime, timedelta
import logging

from .models import Agent

logger = logging.getLogger(__name__)


def _json_contains(column, value: str):
    """SQLite-compatible JSON array contains check."""
    return cast(column, String).like(f'%"{value}"%')


def _text_matches(q: str):
    """
    Build a text filter for a query string.
    Multi-word: OR across all terms (any word matches = relevant result)
    Single word: exact match on the word
    """
    terms = q.lower().split()
    if not terms:
        return None

    # For each term, check across all text fields + JSON fields
    per_term_filters = []
    for term in terms[:6]:
        per_term_filters.append(or_(
            Agent.name.ilike(f"%{term}%"),
            Agent.description.ilike(f"%{term}%"),
            Agent.github_username.ilike(f"%{term}%"),
            cast(Agent.tags, String).ilike(f"%{term}%"),
            cast(Agent.tech_stack, String).ilike(f"%{term}%"),
            cast(Agent.languages, String).ilike(f"%{term}%"),
            cast(Agent.project_domains, String).ilike(f"%{term}%"),
            cast(Agent.specialties, String).ilike(f"%{term}%"),
            cast(Agent.top_submolts, String).ilike(f"%{term}%"),
        ))

    # OR across terms: any match is good
    return or_(*per_term_filters)


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
    query = db.query(Agent)

    if q:
        text_filter = _text_matches(q)
        if text_filter is not None:
            query = query.filter(text_filter)

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
    return {
        "total": total,
        "agents": [_agent_dict(a) for a in agents],
        "offset": offset,
        "limit": limit,
    }
