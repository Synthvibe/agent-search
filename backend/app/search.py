"""
Hybrid search: SQLite full-text + field filtering + Moltbook search API fallback.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, case
from typing import Optional
from datetime import datetime, timedelta
import httpx
import asyncio
import logging

from .models import Agent

logger = logging.getLogger(__name__)

MOLTBOOK_BASE = "https://www.moltbook.com/api/v1"


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
    sort: str = "relevance",
    limit: int = 20,
    offset: int = 0,
) -> dict:
    query = db.query(Agent)

    # Text search
    if q:
        search_term = f"%{q.lower()}%"
        # Search across multiple fields
        text_filter = or_(
            Agent.name.ilike(search_term),
            Agent.description.ilike(search_term),
            Agent.github_username.ilike(search_term),
        )
        # Also check JSON arrays for tags/tech/languages
        query = query.filter(
            or_(
                text_filter,
                func.lower(func.cast(Agent.tags, db.bind.dialect.type_descriptor(None).__class__ if False else Agent.tags.type)).contains(q.lower()),
                func.lower(func.cast(Agent.tech_stack, Agent.tech_stack.type)).contains(q.lower()),
                func.lower(func.cast(Agent.languages, Agent.languages.type)).contains(q.lower()),
                func.lower(func.cast(Agent.project_domains, Agent.project_domains.type)).contains(q.lower()),
            )
        )

    if tag:
        query = query.filter(Agent.tags.contains([tag]))
    if tech:
        query = query.filter(Agent.tech_stack.contains([tech]))
    if domain:
        query = query.filter(Agent.project_domains.contains([domain]))
    if language:
        query = query.filter(Agent.languages.contains([language]))
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
        "karma": Agent.karma.desc(),
        "followers": Agent.follower_count.desc(),
        "engagement": Agent.engagement_rate.desc(),
        "posts": Agent.post_count.desc(),
        "projects": Agent.project_count.desc(),
        "recent": Agent.last_active.desc(),
        "relevance": Agent.karma.desc(),  # fallback for text search
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
