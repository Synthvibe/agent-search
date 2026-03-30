from fastapi import FastAPI, Depends, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
import logging

from .database import get_db, init_db, SessionLocal
from .models import Agent, Post
from .scraper import scrape_all_agents

logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Search", description="Search engine for AI agents", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_indexing = False
_last_indexed: Optional[datetime] = None


@app.on_event("startup")
async def startup():
    init_db()
    # Kick off initial indexing in background
    asyncio.create_task(run_indexing())


async def run_indexing():
    global _indexing, _last_indexed
    if _indexing:
        return
    _indexing = True
    logger.info("Starting agent indexing...")
    try:
        data = await scrape_all_agents(max_posts=2000)
        db = SessionLocal()
        try:
            _upsert_data(db, data)
            _last_indexed = datetime.utcnow()
            logger.info(f"Indexed {len(data['agents'])} agents, {len(data['posts'])} posts")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
    finally:
        _indexing = False


def _upsert_data(db: Session, data: dict):
    for agent_data in data["agents"]:
        existing = db.query(Agent).filter(Agent.id == agent_data["id"]).first()
        if existing:
            for k, v in agent_data.items():
                setattr(existing, k, v)
            existing.updated_at = datetime.utcnow()
        else:
            db.add(Agent(**agent_data))

    for post_data in data["posts"]:
        if not db.query(Post).filter(Post.id == post_data["id"]).first():
            db.add(Post(**post_data))

    db.commit()


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/agents")
def search_agents(
    q: Optional[str] = Query(None, description="Search query"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    verified: Optional[bool] = Query(None, description="Only verified agents"),
    active_days: Optional[int] = Query(None, description="Active within N days"),
    min_karma: Optional[int] = Query(None, description="Minimum karma"),
    sort: str = Query("karma", description="Sort by: karma, followers, posts, engagement, recent"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(Agent)

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Agent.name.ilike(search),
                Agent.description.ilike(search),
            )
        )

    if tag:
        query = query.filter(Agent.tags.contains([tag]))

    if verified is not None:
        query = query.filter(Agent.is_claimed == verified)

    if active_days:
        cutoff = datetime.utcnow() - timedelta(days=active_days)
        query = query.filter(Agent.last_active >= cutoff)

    if min_karma:
        query = query.filter(Agent.karma >= min_karma)

    sort_map = {
        "karma": Agent.karma.desc(),
        "followers": Agent.follower_count.desc(),
        "posts": Agent.post_count.desc(),
        "engagement": Agent.engagement_rate.desc(),
        "recent": Agent.last_active.desc(),
    }
    query = query.order_by(sort_map.get(sort, Agent.karma.desc()))

    total = query.count()
    agents = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "agents": [_agent_to_dict(a) for a in agents],
        "offset": offset,
        "limit": limit,
    }


@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    posts = (
        db.query(Post)
        .filter(Post.agent_id == agent_id)
        .order_by(Post.upvotes.desc())
        .limit(10)
        .all()
    )

    return {
        **_agent_to_dict(agent),
        "recent_posts": [_post_to_dict(p) for p in posts],
    }


@app.get("/api/tags")
def get_tags(db: Session = Depends(get_db)):
    agents = db.query(Agent.tags).all()
    tag_counts = {}
    for (tags,) in agents:
        if tags:
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "total_agents": db.query(Agent).count(),
        "verified_agents": db.query(Agent).filter(Agent.is_claimed == True).count(),
        "total_posts": db.query(Post).count(),
        "last_indexed": _last_indexed.isoformat() if _last_indexed else None,
        "indexing": _indexing,
    }


@app.post("/api/reindex")
async def reindex(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_indexing)
    return {"message": "Reindexing started"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _agent_to_dict(a: Agent) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "description": a.description,
        "avatar_url": a.avatar_url,
        "karma": a.karma,
        "follower_count": a.follower_count,
        "following_count": a.following_count,
        "is_claimed": a.is_claimed,
        "is_active": a.is_active,
        "post_count": a.post_count,
        "total_upvotes": a.total_upvotes,
        "avg_upvotes": round(a.avg_upvotes or 0, 1),
        "engagement_rate": round(a.engagement_rate or 0, 1),
        "tags": a.tags or [],
        "top_submolts": a.top_submolts or [],
        "last_active": a.last_active.isoformat() if a.last_active else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _post_to_dict(p: Post) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "content": p.content[:300] + "..." if p.content and len(p.content) > 300 else p.content,
        "submolt_name": p.submolt_name,
        "upvotes": p.upvotes,
        "score": p.score,
        "comment_count": p.comment_count,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
