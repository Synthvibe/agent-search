"""
Seed script — runs at Docker build time to pre-populate the database.
Scrapes top agents from high-signal submolts AND enriches with GitHub
if GITHUB_TOKEN is available.

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
    has_projects = db.query(Project).count()
    db.close()

    # Check if we need to run GitHub enrichment on an existing seed
    if count > 100 and has_projects > 0:
        logger.info(f"Database already fully seeded: {count} agents, {has_projects} projects.")
        return

    github_token = os.getenv("GITHUB_TOKEN")
    enrich = bool(github_token)

    if count > 100 and has_projects == 0 and enrich:
        logger.info(f"Running GitHub enrichment on {count} existing agents...")
        await _enrich_existing(db)
        return

    logger.info(f"Seeding database from Moltbook (github_enrichment={enrich})...")
    data = await scrape_all_agents(max_posts_total=5000, enrich_github=enrich)

    db = SessionLocal()
    try:
        fields_agent = {c.key for c in Agent.__table__.columns}

        agents_added = 0
        for a in data["agents"]:
            if not db.query(Agent).filter(Agent.id == a["id"]).first():
                db.add(Agent(**{k: v for k, v in a.items() if k in fields_agent}))
                agents_added += 1

        db.commit()
        logger.info(f"Added {agents_added} agents")

        posts_added = 0
        seen_ids: set = set()
        batch = []
        for p in data["posts"]:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                batch.append(Post(**p))
            if len(batch) >= 500:
                db.bulk_save_objects(batch)
                db.commit()
                posts_added += len(batch)
                batch = []
        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            posts_added += len(batch)
        logger.info(f"Added {posts_added} posts")

        fields_proj = {c.key for c in Project.__table__.columns}
        projects_added = 0
        seen_proj_ids: set = set()
        for p in data.get("projects", []):
            if p["id"] not in seen_proj_ids:
                seen_proj_ids.add(p["id"])
                if not db.query(Project).filter(Project.id == p["id"]).first():
                    db.add(Project(**{k: v for k, v in p.items() if k in fields_proj}))
                    projects_added += 1
        db.commit()
        logger.info(f"Added {projects_added} projects")

        final_count = db.query(Agent).count()
        final_proj = db.query(Project).count()
        logger.info(f"Seed complete: {final_count} agents, {posts_added} posts, {final_proj} projects")
    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


async def _enrich_existing(db_unused):
    """Run GitHub enrichment on already-seeded agents."""
    from .database import SessionLocal
    from .models import Agent, Post, Project
    from .github_enricher import enrich_agent

    db = SessionLocal()
    try:
        agents = db.query(Agent).order_by(Agent.karma.desc()).all()
        fields_proj = {c.key for c in Project.__table__.columns}
        total_projects = 0

        for i, agent in enumerate(agents):
            posts = db.query(Post).filter(Post.agent_id == agent.id).all()
            post_text = " ".join(f"{p.title} {p.content}" for p in posts)
            agent_dict = {
                "id": agent.id, "name": agent.name,
                "description": agent.description or "",
            }
            try:
                enriched, projects = await enrich_agent(agent_dict, post_text)
                agent.github_username = enriched.get("github_username")
                agent.github_url = enriched.get("github_url")
                agent.languages = enriched.get("languages", [])
                agent.tech_stack = enriched.get("tech_stack", [])
                agent.project_domains = enriched.get("project_domains", [])
                agent.project_count = len(projects)
                total_projects += len(projects)

                for p in projects:
                    if not db.query(Project).filter(Project.id == p["id"]).first():
                        db.add(Project(**{k: v for k, v in p.items() if k in fields_proj}))
            except Exception as e:
                logger.debug(f"Enrichment failed for {agent.name}: {e}")

            if i % 50 == 0 and i > 0:
                db.commit()
                logger.info(f"  GitHub enrichment {i}/{len(agents)}, {total_projects} projects...")
                await asyncio.sleep(2)

        db.commit()
        logger.info(f"GitHub enrichment complete: {total_projects} projects added")
    finally:
        db.close()


from .scraper import scrape_all_agents  # noqa
from .models import Post, Project  # noqa

if __name__ == "__main__":
    asyncio.run(seed())
