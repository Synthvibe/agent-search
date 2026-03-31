"""
Seed script — runs at Docker build time to pre-populate the database.
Scrapes top agents from high-signal submolts so the service is immediately
useful on cold start, with no indexing delay.

Run: python -m app.seed
"""
import asyncio
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Use a persistent path for the seeded DB
SEED_DB_PATH = "/app/seed_data/agenthub.db"


async def seed():
    # Set DB path before imports
    os.environ["DATABASE_URL"] = f"sqlite:///{SEED_DB_PATH}"
    os.makedirs("/app/seed_data", exist_ok=True)

    from .database import init_db, SessionLocal
    from .models import Agent
    from .scraper import scrape_all_agents

    init_db()

    # Check if already seeded
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
        from .models import Post, Project
        fields_agent = {c.key for c in Agent.__table__.columns}
        fields_proj = {c.key for c in Project.__table__.columns}

        for a in data["agents"]:
            if not db.query(Agent).filter(Agent.id == a["id"]).first():
                db.add(Agent(**{k: v for k, v in a.items() if k in fields_agent}))

        for p in data["posts"]:
            if not db.query(Post).filter(Post.id == p["id"]).first():
                db.add(Post(**p))

        for p in data.get("projects", []):
            if not db.query(Project).filter(Project.id == p["id"]).first():
                db.add(Project(**{k: v for k, v in p.items() if k in fields_proj}))

        db.commit()
        final_count = db.query(Agent).count()
        logger.info(f"Seeded {final_count} agents, {len(data['posts'])} posts, {len(data.get('projects', []))} projects")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed())
