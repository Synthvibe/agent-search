"""
Enriches agent profiles with GitHub project data.
Extracts GitHub usernames from Moltbook descriptions/posts, then fetches repos.
"""
import httpx
import re
import os
import asyncio
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

GITHUB_URL_PATTERNS = [
    re.compile(r'github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})(?:/([a-zA-Z0-9_.-]+))?', re.IGNORECASE),
    re.compile(r'@([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})\s+on\s+github', re.IGNORECASE),
]

TECH_KEYWORDS = {
    # Languages
    "Python": ["python", ".py", "flask", "django", "fastapi", "pytorch", "tensorflow"],
    "TypeScript": ["typescript", ".ts", "tsx"],
    "JavaScript": ["javascript", ".js", "nodejs", "node.js", "npm"],
    "Rust": ["rust", ".rs", "cargo"],
    "Go": ["golang", " go ", ".go"],
    "Ruby": ["ruby", "rails", ".rb"],
    "Java": [" java ", "spring boot", "gradle", "maven"],
    "C++": ["c++", "cpp", ".cpp"],
    # Frameworks / tools
    "React": ["react", "nextjs", "next.js"],
    "Vue": ["vue", "nuxt"],
    "Docker": ["docker", "container", "dockerfile"],
    "FastAPI": ["fastapi"],
    "LangChain": ["langchain"],
    "OpenAI": ["openai", "gpt-4", "gpt-3"],
    "Anthropic": ["anthropic", "claude"],
    "PostgreSQL": ["postgres", "postgresql"],
    "Redis": ["redis"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "AWS": ["aws ", "lambda", "s3 ", "ec2"],
    "GCP": ["gcp", "google cloud", "cloud run", "bigquery"],
}

PROJECT_DOMAIN_KEYWORDS = {
    "web": ["website", "webapp", "frontend", "backend", "api", "nextjs", "react", "vue", "html", "css"],
    "ml": ["machine learning", "ml", "model", "training", "neural", "pytorch", "tensorflow", "huggingface", "llm", "embedding"],
    "automation": ["automation", "bot", "scraper", "crawler", "pipeline", "workflow", "cron"],
    "data": ["data", "analytics", "dashboard", "visualization", "pandas", "spark", "etl", "database"],
    "devtools": ["cli", "tool", "library", "sdk", "plugin", "extension", "package"],
    "agent": ["agent", "autonomous", "multi-agent", "orchestration", "agentic"],
    "mobile": ["ios", "android", "react native", "flutter", "mobile app"],
    "infrastructure": ["infrastructure", "devops", "deployment", "terraform", "kubernetes", "docker"],
    "security": ["security", "auth", "encryption", "vulnerability", "penetration"],
    "game": ["game", "simulation", "unity", "unreal"],
}


def extract_github_usernames(text: str) -> list[str]:
    """Extract potential GitHub usernames from text."""
    if not text:
        return []
    usernames = []
    for pattern in GITHUB_URL_PATTERNS:
        for match in pattern.finditer(text):
            username = match.group(1)
            if username and username.lower() not in ('blob', 'tree', 'commit', 'issues', 'pulls', 'org'):
                usernames.append(username)
    return list(set(usernames))


def extract_tech_stack(text: str) -> list[str]:
    text_lower = text.lower()
    return [tech for tech, keywords in TECH_KEYWORDS.items() if any(kw in text_lower for kw in keywords)]


def extract_project_domains(text: str) -> list[str]:
    text_lower = text.lower()
    return [domain for domain, keywords in PROJECT_DOMAIN_KEYWORDS.items() if any(kw in text_lower for kw in keywords)]


def parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


async def fetch_github_repos(client: httpx.AsyncClient, username: str) -> list[dict]:
    """Fetch public repos for a GitHub user."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        resp = await client.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"type": "owner", "per_page": 100, "sort": "updated"},
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"GitHub fetch failed for {username}: {e}")
        return []


async def fetch_repo_languages(client: httpx.AsyncClient, full_name: str) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    try:
        resp = await client.get(f"{GITHUB_API}/repos/{full_name}/languages", headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def repos_to_projects(username: str, repos: list[dict], agent_id: str) -> list[dict]:
    """Convert GitHub API repo objects to our Project schema."""
    projects = []
    for repo in repos:
        if repo.get("fork"):
            continue  # skip forks for portfolio purposes

        text = f"{repo.get('name', '')} {repo.get('description', '') or ''} {' '.join(repo.get('topics', []))}"
        projects.append({
            "id": f"gh_{repo['id']}",
            "agent_id": agent_id,
            "name": repo["name"],
            "description": repo.get("description") or "",
            "url": repo.get("html_url"),
            "source": "github",
            "language": repo.get("language"),
            "languages": [],  # populated separately if needed
            "topics": repo.get("topics", []),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "is_fork": repo.get("fork", False),
            "tags": list(set(extract_project_domains(text))),
            "created_at": parse_dt(repo.get("created_at")),
            "updated_at": parse_dt(repo.get("updated_at")),
        })
    return projects


async def enrich_agent(agent_data: dict, all_post_text: str) -> dict:
    """
    Given agent data + their post text, find GitHub and enrich with project data.
    Returns updated agent fields + list of projects.
    """
    combined_text = (agent_data.get("description") or "") + " " + all_post_text
    github_usernames = extract_github_usernames(combined_text)

    projects = []
    github_username = None
    all_repo_text = ""

    if github_usernames:
        async with httpx.AsyncClient() as client:
            for username in github_usernames[:2]:  # max 2 to avoid rate limits
                repos = await fetch_github_repos(client, username)
                if repos:
                    github_username = username
                    new_projects = repos_to_projects(username, repos, agent_data["id"])
                    projects.extend(new_projects)
                    all_repo_text += " ".join(
                        f"{r.get('name', '')} {r.get('description', '') or ''} {' '.join(r.get('topics', []))}"
                        for r in repos
                    )
                    await asyncio.sleep(0.3)
                    break

    full_text = combined_text + " " + all_repo_text
    tech_stack = extract_tech_stack(full_text)
    project_domains = extract_project_domains(full_text)
    languages = list(set(
        p["language"] for p in projects if p.get("language")
    ))

    enriched = {
        **agent_data,
        "github_username": github_username,
        "github_url": f"https://github.com/{github_username}" if github_username else None,
        "project_count": len(projects),
        "languages": languages,
        "tech_stack": tech_stack,
        "project_domains": project_domains,
    }

    return enriched, projects
