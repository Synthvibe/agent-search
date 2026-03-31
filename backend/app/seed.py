"""
Seed script — runs at Docker build time to pre-populate the database.
Scrapes top agents from high-signal submolts so the service is immediately
useful on cold start, with no indexing delay.

Run: python -m app.seed
"""
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEED_DB_PATH = "/app/seed_data/agenthub.db"


async def seed():
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{SEED_DB_PATH}")
    os.makedirs("/app/seed_data", exist_ok=True)

    from .database import init_db, SessionLocal
    from .models import Agent, Post, Project

    init_db()

    db = SessionLocal()
    count = db.query(Agent).count()
    db.close()

    if count > 100:
        logger.info(f"Database already seeded with {count} agents, skipping.")
        return

    logger.info("Seeding database from Moltbook...")
    data = await scrape_all_agents(max_posts_total=5000, enrich_github=True)

    db = SessionLocal()
    try:
        fields_agent = {c.key for c in Agent.__table__.columns}
        fields_proj = {c.key for c in Project.__table__.columns}

        agents_added = 0
        for a in data["agents"]:
            if not db.query(Agent).filter(Agent.id == a["id"]).first():
                db.add(Agent(**{k: v for k, v in a.items() if k in fields_agent}))
                agents_added += 1
        db.flush()

        posts_added = 0
        seen_post_ids = set()
        for p in data["posts"]:
            if p["id"] not in seen_post_ids and not db.query(Post).filter(Post.id == p["id"]).first():
                db.add(Post(**p))
                seen_post_ids.add(p["id"])
                posts_added += 1

        projects_added = 0
        for p in data.get("projects", []):
            if not db.query(Project).filter(Project.id == p["id"]).first():
                db.add(Project(**{k: v for k, v in p.items() if k in fields_proj}))
                projects_added += 1

        db.commit()
        logger.info(f"Seeded: {agents_added} agents, {posts_added} posts, {projects_added} projects")
    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


# Import here to avoid circular at module level
from .scraper import scrape_all_agents  # noqa: E402

if __name__ == "__main__":
    asyncio.run(seed())
