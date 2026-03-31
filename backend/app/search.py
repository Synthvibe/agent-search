"""
Hybrid search for AgentHub.

SQLite doesn't support JSON array contains natively, so we use LIKE on the
JSON string representation for tag/tech/language/domain filtering.
Text search uses ILIKE on name + description.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, cast, String
from typing import Optional
from datetime import datetime, timedelta
import logging

from .models import Agent

logger = logging.getLogger(__name__)


def _json_contains(column, value: str) -> object:
    """SQLite-compatible JSON array contains check using string matching."""
    # JSON arrays are stored as '["val1", "val2"]'
    # We match '"value"' to avoid partial matches (e.g. "Go" matching "Golang")
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
    query = db.query(Agent)

    # Text search across name, description, github username
    if q:
        q_lower = q.lower()
        terms = q_lower.split()

        # Build OR across all text fields and JSON columns for each term
        term_filters = []
        for term in terms[:5]:  # max 5 terms
            term_filter = or_(
                Agent.name.ilike(f"%{term}%"),
                Agent.description.ilike(f"%{term}%"),
                Agent.github_username.ilike(f"%{term}%"),
                cast(Agent.tags, String).ilike(f"%{term}%"),
                cast(Agent.tech_stack, String).ilike(f"%{term}%"),
                cast(Agent.languages, String).ilike(f"%{term}%"),
                cast(Agent.project_domains, String).ilike(f"%{term}%"),
                cast(Agent.specialties, String).ilike(f"%{term}%"),
            )
            term_filters.append(term_filter)

        # AND across terms (all terms must match somewhere)
        if term_filters:
            query = query.filter(and_(*term_filters))

    # Exact JSON array filters
    if tag:
        query = query.filter(_json_contains(Agent.tags, tag))
    if tech:
        query = query.filter(_json_contains(Agent.tech_stack, tech))
    if domain:
        query = query.filter(_json_contains(Agent.project_domains, domain))
    if language:
        query = query.filter(_json_contains(Agent.languages, language))

    # Boolean/scalar filters
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

    # Sorting
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
