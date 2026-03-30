import httpx
import asyncio
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

MOLTBOOK_BASE = "https://www.moltbook.com/api/v1"

DOMAIN_TAGS = {
    "coding": ["code", "python", "javascript", "typescript", "rust", "golang", "api", "github", "deploy", "docker", "backend", "frontend", "database", "sql", "programming", "dev", "software"],
    "research": ["research", "paper", "study", "analysis", "data", "science", "experiment", "hypothesis", "findings", "arxiv", "academic"],
    "writing": ["writing", "blog", "article", "post", "essay", "draft", "edit", "content", "story", "narrative"],
    "automation": ["automation", "workflow", "cron", "schedule", "pipeline", "script", "task", "job", "trigger", "orchestrat"],
    "memory": ["memory", "context", "remember", "recall", "store", "retriev", "embed", "vector", "rag", "knowledge"],
    "social": ["social", "community", "engage", "follow", "comment", "upvote", "moltbook", "share", "interact"],
    "finance": ["finance", "trading", "market", "stock", "crypto", "investment", "portfolio", "price", "economic"],
    "productivity": ["productivity", "calendar", "email", "meeting", "schedule", "organiz", "plan", "task manager"],
    "creative": ["creative", "art", "music", "design", "generate", "imagine", "visual", "image", "draw", "compose"],
    "reasoning": ["reasoning", "logic", "think", "argue", "debate", "philosophy", "ethics", "decision"],
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


async def fetch_posts_page(client: httpx.AsyncClient, cursor: Optional[str] = None, limit: int = 100) -> dict:
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    resp = await client.get(f"{MOLTBOOK_BASE}/posts", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


async def scrape_all_agents(max_posts: int = 2000, enrich_github: bool = True) -> dict:
    """Scrape posts from Moltbook, extract unique agents with stats."""
    from .github_enricher import enrich_agent

    agents = {}
    agent_post_texts = {}  # agent_id -> all post text for enrichment
    posts_data = []
    cursor = None
    fetched = 0

    async with httpx.AsyncClient() as client:
        while fetched < max_posts:
            try:
                data = await fetch_posts_page(client, cursor=cursor, limit=100)
            except Exception as e:
                logger.error(f"Error fetching posts: {e}")
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
                    "submolt_name": post.get("submolt", {}).get("name", ""),
                    "upvotes": post.get("upvotes", 0),
                    "downvotes": post.get("downvotes", 0),
                    "score": post.get("score", 0),
                    "comment_count": post.get("comment_count", 0),
                    "created_at": parse_datetime(post.get("created_at")),
                }
                posts_data.append(post_record)

                if agent_id not in agents:
                    agents[agent_id] = {
                        "id": agent_id,
                        "name": author.get("name", ""),
                        "description": author.get("description", "") or "",
                        "avatar_url": author.get("avatarUrl"),
                        "karma": author.get("karma", 0),
                        "follower_count": author.get("followerCount", 0),
                        "following_count": author.get("followingCount", 0),
                        "is_claimed": author.get("isClaimed", False),
                        "is_active": author.get("isActive", True),
                        "created_at": parse_datetime(author.get("createdAt")),
                        "last_active": parse_datetime(author.get("lastActive")),
                        "post_count": 0,
                        "total_upvotes": 0,
                        "submolts": {},
                        # will be set by enricher
                        "github_username": None,
                        "github_url": None,
                        "project_count": 0,
                        "languages": [],
                        "tech_stack": [],
                        "project_domains": [],
                    }
                    agent_post_texts[agent_id] = ""

                agents[agent_id]["post_count"] += 1
                agents[agent_id]["total_upvotes"] += post.get("upvotes", 0)
                agent_post_texts[agent_id] += " " + post_text

                submolt = post.get("submolt", {}).get("name", "")
                if submolt:
                    agents[agent_id]["submolts"][submolt] = agents[agent_id]["submolts"].get(submolt, 0) + 1

            fetched += len(posts)
            cursor = data.get("next_cursor")
            if not data.get("has_more") or not cursor:
                break

            logger.info(f"Fetched {fetched} posts, {len(agents)} unique agents so far...")
            await asyncio.sleep(0.3)

    # Compute base stats
    for agent in agents.values():
        pc = agent["post_count"]
        agent["avg_upvotes"] = agent["total_upvotes"] / pc if pc > 0 else 0
        agent["engagement_rate"] = agent["avg_upvotes"]
        agent["top_submolts"] = sorted(agent["submolts"].items(), key=lambda x: x[1], reverse=True)[:5]
        agent["top_submolts"] = [s[0] for s in agent["top_submolts"]]

        all_text = agent.get("description", "") + " " + agent_post_texts.get(agent["id"], "")
        agent["tags"] = list(set(extract_tags(all_text)))
        del agent["submolts"]

    all_projects = []

    # GitHub enrichment (rate-limited)
    if enrich_github:
        logger.info(f"Enriching {len(agents)} agents with GitHub data...")
        for i, (agent_id, agent) in enumerate(agents.items()):
            try:
                enriched, projects = await enrich_agent(agent, agent_post_texts.get(agent_id, ""))
                agents[agent_id] = enriched
                all_projects.extend(projects)
            except Exception as e:
                logger.warning(f"Enrichment failed for {agent_id}: {e}")

            if i > 0 and i % 10 == 0:
                logger.info(f"Enriched {i}/{len(agents)} agents...")
                await asyncio.sleep(1)  # respect GitHub rate limits

    logger.info(f"Done. {fetched} posts, {len(agents)} agents, {len(all_projects)} projects")
    return {
        "agents": list(agents.values()),
        "posts": posts_data,
        "projects": all_projects,
    }
