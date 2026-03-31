"""
AgentHub Scraper — indexes battle-hardened builders from Moltbook.

Strategy:
1. Primary: `builds` submolt — agents who have actually shipped things
2. Secondary: `tooling`, `agents`, `openclaw-explorers` — high-signal communities
3. Profile enrichment: Moltbook profile API for owner X handles
4. GitHub enrichment: repos linked from profiles/posts
5. Quality filter: min karma threshold, active within 90 days
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

MOLTBOOK_BASE = "https://www.moltbook.com/api/v1"

# Submolts ordered by signal quality for our use case
SCRAPE_PLAN = [
    {"submolt": "builds",             "limit": 2000, "sort": "top"},
    {"submolt": "tooling",            "limit": 500,  "sort": "top"},
    {"submolt": "agents",             "limit": 500,  "sort": "top"},
    {"submolt": "openclaw-explorers", "limit": 300,  "sort": "top"},
    {"submolt": "introductions",      "limit": 300,  "sort": "new"},
]

# Minimum quality bar for inclusion
MIN_KARMA = 50
MIN_LAST_ACTIVE_DAYS = 180  # 6 months

DOMAIN_TAGS = {
    "coding":         ["code", "python", "javascript", "typescript", "rust", "golang", "api", "github", "deploy", "docker", "backend", "frontend", "database", "sql", "programming", "dev", "software", "build", "shipped"],
    "research":       ["research", "paper", "study", "analysis", "data", "science", "experiment", "hypothesis", "findings", "arxiv", "academic", "report"],
    "writing":        ["writing", "blog", "article", "post", "essay", "draft", "edit", "content", "story", "narrative", "docs", "documentation"],
    "automation":     ["automation", "workflow", "cron", "schedule", "pipeline", "script", "task", "job", "trigger", "orchestrat", "agentic", "autonomous"],
    "memory":         ["memory", "context", "remember", "recall", "store", "retriev", "embed", "vector", "rag", "knowledge"],
    "social":         ["social", "community", "engage", "follow", "comment", "upvote", "moltbook", "share", "interact", "network"],
    "finance":        ["finance", "trading", "market", "stock", "crypto", "investment", "portfolio", "price", "economic", "defi", "wallet"],
    "productivity":   ["productivity", "calendar", "email", "meeting", "schedule", "organiz", "plan", "assistant", "summarize"],
    "creative":       ["creative", "art", "music", "design", "generate", "imagine", "visual", "image", "draw", "compose", "generative"],
    "reasoning":      ["reasoning", "logic", "think", "argue", "debate", "philosophy", "ethics", "decision", "analysis"],
    "security":       ["security", "pentest", "ctf", "exploit", "vulnerability", "bug bounty", "hacking", "cipher", "cryptography"],
    "infrastructure": ["infrastructure", "devops", "kubernetes", "terraform", "cloud", "deployment", "server", "container", "aws", "gcp", "azure"],
}


def extract_tags(text: str) -> list[str]:
    text_lower = text.lower()
    return [tag for tag, keywords in DOMAIN_TAGS.items() if any(kw in text_lower for kw in keywords)]


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


async def fetch_posts_page(client: httpx.AsyncClient, submolt: str, sort: str = "top",
                            cursor: Optional[str] = None, limit: int = 100) -> dict:
    params = {"limit": min(100, limit), "submolt": submolt, "sort": sort}
    if cursor:
        params["cursor"] = cursor
    resp = await client.get(f"{MOLTBOOK_BASE}/posts", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


async def fetch_agent_profile(client: httpx.AsyncClient, name: str) -> Optional[dict]:
    try:
        resp = await client.get(f"{MOLTBOOK_BASE}/agents/profile", params={"name": name}, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("agent")
    except Exception as e:
        logger.debug(f"Profile fetch failed for {name}: {e}")
        return None


def is_quality_agent(agent: dict) -> bool:
    """Filter to only include battle-hardened builders."""
    if agent.get("karma", 0) < MIN_KARMA:
        return False
    last_active = agent.get("last_active")
    if last_active:
        cutoff = datetime.utcnow() - timedelta(days=MIN_LAST_ACTIVE_DAYS)
        if last_active < cutoff:
            return False
    return True


async def scrape_all_agents(max_posts_total: int = 5000, enrich_github: bool = True) -> dict:
    from .github_enricher import enrich_agent

    agents: dict = {}
    agent_post_texts: dict = {}
    posts_data: list = []
    total_fetched = 0

    async with httpx.AsyncClient() as client:
        for plan in SCRAPE_PLAN:
            submolt = plan["submolt"]
            limit = min(plan["limit"], max(100, max_posts_total - total_fetched))
            sort = plan["sort"]
            fetched_this = 0
            cursor = None

            logger.info(f"Scraping m/{submolt} (limit={limit}, sort={sort})")

            while fetched_this < limit:
                try:
                    data = await fetch_posts_page(client, submolt, sort, cursor, min(100, limit - fetched_this))
                except Exception as e:
                    logger.warning(f"Error fetching m/{submolt}: {e}")
                    break

                posts = data.get("posts", [])
                if not posts:
                    break

                for post in posts:
                    author = post.get("author", {})
                    agent_id = author.get("id")
                    if not agent_id:
                        continue

                    post_text = f"{post.get('title', '')} {post.get('content', '')}"
                    post_record = {
                        "id": post["id"],
                        "agent_id": agent_id,
                        "title": post.get("title", ""),
                        "content": post.get("content", ""),
                        "submolt_name": submolt,
                        "upvotes": post.get("upvotes", 0),
                        "downvotes": post.get("downvotes", 0),
                        "score": post.get("score", 0),
                        "comment_count": post.get("comment_count", 0),
                        "created_at": parse_datetime(post.get("created_at")),
                    }
                    posts_data.append(post_record)

                    if agent_id not in agents:
                        last_active = parse_datetime(author.get("lastActive"))
                        agents[agent_id] = {
                            "id": agent_id,
                            "name": author.get("name", ""),
                            "description": author.get("description", "") or "",
                            "avatar_url": author.get("avatarUrl"),
                            "karma": author.get("karma", 0),
                            "follower_count": author.get("followerCount", 0),
                            "following_count": author.get("followingCount", 0),
                            "posts_count": 0,
                            "comments_count": 0,
                            "is_claimed": author.get("isClaimed", False),
                            "is_active": author.get("isActive", True),
                            "created_at": parse_datetime(author.get("createdAt")),
                            "last_active": last_active,
                            "x_handle": None,
                            "x_name": None,
                            "x_avatar": None,
                            "post_count": 0,
                            "total_upvotes": 0,
                            "submolts_seen": {},
                            "github_username": None,
                            "github_url": None,
                            "project_count": 0,
                            "languages": [],
                            "tech_stack": [],
                            "project_domains": [],
                            "availability": "unknown",
                            "rate": None,
                            "specialties": [],
                            "contact_preference": "moltbook",
                        }
                        agent_post_texts[agent_id] = ""

                    agents[agent_id]["post_count"] += 1
                    agents[agent_id]["total_upvotes"] += post.get("upvotes", 0)
                    agents[agent_id]["submolts_seen"][submolt] = agents[agent_id]["submolts_seen"].get(submolt, 0) + 1
                    agent_post_texts[agent_id] += " " + post_text

                fetched_this += len(posts)
                total_fetched += len(posts)
                cursor = data.get("next_cursor")
                if not data.get("has_more") or not cursor:
                    break
                await asyncio.sleep(0.3)

            logger.info(f"  → {fetched_this} posts, {len(agents)} unique agents total")

    # Apply quality filter
    filtered = {k: v for k, v in agents.items() if is_quality_agent(v)}
    logger.info(f"Quality filter: {len(agents)} → {len(filtered)} agents (min_karma={MIN_KARMA})")
    agents = filtered

    # Compute base stats
    for agent_id, agent in agents.items():
        pc = agent["post_count"]
        agent["avg_upvotes"] = agent["total_upvotes"] / pc if pc > 0 else 0
        agent["engagement_rate"] = agent["avg_upvotes"]
        agent["top_submolts"] = sorted(agent["submolts_seen"].items(), key=lambda x: x[1], reverse=True)[:5]
        agent["top_submolts"] = [s[0] for s in agent["top_submolts"]]
        all_text = agent.get("description", "") + " " + agent_post_texts.get(agent_id, "")
        agent["tags"] = list(set(extract_tags(all_text)))
        del agent["submolts_seen"]

    # Fetch full profiles for top 300 agents
    top_agents = sorted(agents.values(), key=lambda a: a["karma"], reverse=True)[:300]
    logger.info(f"Fetching full Moltbook profiles for top {len(top_agents)} agents...")
    async with httpx.AsyncClient() as client:
        for i, agent in enumerate(top_agents):
            profile = await fetch_agent_profile(client, agent["name"])
            if profile:
                agents[agent["id"]].update({
                    "posts_count": profile.get("posts_count", 0),
                    "comments_count": profile.get("comments_count", 0),
                    "karma": profile.get("karma", agent["karma"]),
                    "follower_count": profile.get("follower_count", agent["follower_count"]),
                    "is_claimed": profile.get("is_claimed", agent["is_claimed"]),
                })
                owner = profile.get("owner") or {}
                if owner.get("x_handle"):
                    agents[agent["id"]].update({
                        "x_handle": owner.get("x_handle"),
                        "x_name": owner.get("x_name"),
                        "x_avatar": owner.get("x_avatar"),
                    })
            if i % 30 == 0 and i > 0:
                logger.info(f"  Profile fetch {i}/{len(top_agents)}...")
                await asyncio.sleep(1)

    # GitHub enrichment
    all_projects = []
    if enrich_github:
        logger.info(f"GitHub enrichment for {len(agents)} agents...")
        for i, (agent_id, agent) in enumerate(agents.items()):
            try:
                enriched, projects = await enrich_agent(agent, agent_post_texts.get(agent_id, ""))
                agents[agent_id] = enriched
                all_projects.extend(projects)
            except Exception as e:
                logger.debug(f"GitHub enrichment failed for {agent_id}: {e}")
            if i > 0 and i % 20 == 0:
                await asyncio.sleep(1)
                if i % 100 == 0:
                    logger.info(f"  GitHub enrichment {i}/{len(agents)}, {len(all_projects)} projects found...")

    logger.info(f"Scrape complete: {len(agents)} quality agents, {len(posts_data)} posts, {len(all_projects)} projects")
    return {"agents": list(agents.values()), "posts": posts_data, "projects": all_projects}
