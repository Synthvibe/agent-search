"""
AgentHub API Tests

Tests cover:
- Search correctness and relevance
- Filter combinations
- Agent profile retrieval
- Proposal flow
- Edge cases and error handling
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

from ..models import Base, Agent, Post, Project, Proposal
from ..database import get_db
from ..main import app

# ── Test DB setup ────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_agenthub.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    # Seed test agents
    agents = [
        Agent(
            id="agent-1", name="PyMLBot", karma=50000,
            description="Python machine learning researcher. Builds neural nets and data pipelines.",
            is_claimed=True, is_active=True,
            follower_count=1200, post_count=45, total_upvotes=5000,
            avg_upvotes=111.0, engagement_rate=111.0,
            tags=["coding", "research", "automation"],
            languages=["Python"], tech_stack=["Python", "PyTorch", "FastAPI"],
            project_domains=["ml", "data"], project_count=8,
            github_username="pymlbot", github_url="https://github.com/pymlbot",
            availability="available", rate="50 tokens/hr",
            last_active=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow() - timedelta(days=90),
        ),
        Agent(
            id="agent-2", name="ReactBuilder", karma=30000,
            description="Frontend specialist. I build React dashboards and Next.js apps.",
            is_claimed=True, is_active=True,
            follower_count=800, post_count=30, total_upvotes=2500,
            avg_upvotes=83.0, engagement_rate=83.0,
            tags=["coding", "creative"],
            languages=["TypeScript", "JavaScript"],
            tech_stack=["React", "TypeScript", "Next.js", "Tailwind"],
            project_domains=["web"], project_count=12,
            availability="busy",
            last_active=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=60),
        ),
        Agent(
            id="agent-3", name="AutomateEverything", karma=15000,
            description="Automation and workflow specialist. If it can be scripted, I've scripted it.",
            is_claimed=False, is_active=True,
            follower_count=400, post_count=20, total_upvotes=800,
            avg_upvotes=40.0, engagement_rate=40.0,
            tags=["automation", "coding"],
            languages=["Python", "Go"], tech_stack=["Docker", "Python", "Kubernetes"],
            project_domains=["automation", "infrastructure"], project_count=5,
            availability="available",
            last_active=datetime.utcnow() - timedelta(days=3),
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
        Agent(
            id="agent-4", name="InactiveAgent", karma=100,
            description="An old agent who hasn't been around.",
            is_claimed=False, is_active=False,
            follower_count=5, post_count=1, total_upvotes=2,
            avg_upvotes=2.0, engagement_rate=2.0,
            tags=[], languages=[], tech_stack=[], project_domains=[],
            project_count=0, availability="unknown",
            last_active=datetime.utcnow() - timedelta(days=120),
            created_at=datetime.utcnow() - timedelta(days=365),
        ),
    ]
    for a in agents:
        db.add(a)

    # Seed projects
    db.add(Project(
        id="proj-1", agent_id="agent-1", name="neural-pipeline",
        description="End-to-end ML training pipeline", source="github",
        language="Python", topics=["machine-learning", "pytorch"], stars=45,
        tags=["ml", "automation"],
    ))
    db.add(Project(
        id="proj-2", agent_id="agent-2", name="agent-dashboard",
        description="React dashboard for monitoring AI agents", source="github",
        language="TypeScript", topics=["react", "dashboard"], stars=120,
        tags=["web", "devtools"],
    ))

    # Seed posts
    db.add(Post(
        id="post-1", agent_id="agent-1", title="Built a Python ML pipeline",
        content="Here's how I built a complete ML training pipeline with PyTorch...",
        submolt_name="builds", upvotes=200, comment_count=45,
        created_at=datetime.utcnow() - timedelta(days=10),
    ))

    db.commit()
    yield
    db.close()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Health ───────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_stats():
    r = client.get("/api/stats")
    assert r.status_code == 200
    d = r.json()
    assert d["total_agents"] == 4
    assert d["verified_agents"] == 2


# ── Search ───────────────────────────────────────────────────────────────────

def test_search_all():
    r = client.get("/api/agents")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 4
    assert len(d["agents"]) == 4


def test_search_by_name():
    r = client.get("/api/agents?q=PyMLBot")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert any(a["name"] == "PyMLBot" for a in agents)


def test_search_by_description_keyword():
    r = client.get("/api/agents?q=machine+learning")
    assert r.status_code == 200
    agents = r.json()["agents"]
    names = [a["name"] for a in agents]
    assert "PyMLBot" in names, "Should find ML agent by description keyword"


def test_search_by_tech():
    r = client.get("/api/agents?tech=React")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert len(agents) >= 1
    assert any(a["name"] == "ReactBuilder" for a in agents)


def test_search_by_language():
    r = client.get("/api/agents?language=TypeScript")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert all("TypeScript" in a["languages"] for a in agents)


def test_search_by_domain():
    r = client.get("/api/agents?domain=ml")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert any(a["name"] == "PyMLBot" for a in agents)


def test_filter_verified_only():
    r = client.get("/api/agents?verified=true")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert all(a["is_claimed"] for a in agents)
    assert len(agents) == 2


def test_filter_has_projects():
    r = client.get("/api/agents?has_projects=true")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert all(a["project_count"] > 0 for a in agents)


def test_filter_available():
    r = client.get("/api/agents?availability=available")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert all(a["availability"] == "available" for a in agents)
    assert len(agents) == 2


def test_filter_active_days():
    r = client.get("/api/agents?active_days=2")
    assert r.status_code == 200
    agents = r.json()["agents"]
    # Only PyMLBot (2h ago) and ReactBuilder (1d ago) qualify
    names = [a["name"] for a in agents]
    assert "PyMLBot" in names
    assert "ReactBuilder" in names
    assert "InactiveAgent" not in names


def test_filter_min_karma():
    r = client.get("/api/agents?min_karma=20000")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert all(a["karma"] >= 20000 for a in agents)
    assert len(agents) == 2


def test_combined_filters():
    r = client.get("/api/agents?verified=true&has_projects=true&language=Python")
    assert r.status_code == 200
    agents = r.json()["agents"]
    # PyMLBot: verified, has projects, Python
    assert len(agents) >= 1
    assert any(a["name"] == "PyMLBot" for a in agents)


def test_sort_by_karma():
    r = client.get("/api/agents?sort=karma")
    assert r.status_code == 200
    agents = r.json()["agents"]
    karmas = [a["karma"] for a in agents]
    assert karmas == sorted(karmas, reverse=True)


def test_sort_by_projects():
    r = client.get("/api/agents?sort=projects")
    assert r.status_code == 200
    agents = r.json()["agents"]
    counts = [a["project_count"] for a in agents]
    assert counts == sorted(counts, reverse=True)


def test_sort_by_recent():
    r = client.get("/api/agents?sort=recent")
    assert r.status_code == 200
    agents = r.json()["agents"]
    # First result should be most recently active
    assert agents[0]["name"] == "PyMLBot"


def test_pagination():
    r1 = client.get("/api/agents?limit=2&offset=0")
    r2 = client.get("/api/agents?limit=2&offset=2")
    assert r1.status_code == 200
    assert r2.status_code == 200
    ids1 = {a["id"] for a in r1.json()["agents"]}
    ids2 = {a["id"] for a in r2.json()["agents"]}
    assert ids1.isdisjoint(ids2), "Pages should not overlap"


def test_empty_search_results():
    r = client.get("/api/agents?q=xyznonexistentquery12345")
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ── Agent Profile ─────────────────────────────────────────────────────────────

def test_get_agent_by_id():
    r = client.get("/api/agents/agent-1")
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "PyMLBot"
    assert "projects" in d
    assert "top_posts" in d
    assert "moltbook_url" in d


def test_get_agent_by_name():
    r = client.get("/api/agents/ReactBuilder")
    assert r.status_code == 200
    assert r.json()["name"] == "ReactBuilder"


def test_get_agent_projects():
    r = client.get("/api/agents/agent-1")
    d = r.json()
    assert len(d["projects"]) >= 1
    assert d["projects"][0]["name"] == "neural-pipeline"


def test_get_agent_not_found():
    r = client.get("/api/agents/nonexistent-agent-xyz")
    assert r.status_code == 404


def test_get_agent_top_posts():
    r = client.get("/api/agents/agent-1")
    d = r.json()
    assert len(d["top_posts"]) >= 1
    assert d["top_posts"][0]["submolt_name"] == "builds"


def test_similar_agents():
    r = client.get("/api/agents/agent-1/similar")
    assert r.status_code == 200
    similar = r.json()
    assert isinstance(similar, list)
    # Should not include the agent itself
    assert not any(a["id"] == "agent-1" for a in similar)


# ── Proposals ─────────────────────────────────────────────────────────────────

def test_send_proposal():
    params = {
        "target_agent_id": "agent-1",
        "from_agent_name": "BuilderBot3000",
        "from_agent_description": "I build SaaS products",
        "project_name": "AgentOS",
        "project_description": "An operating system for AI agents",
        "message": "You'd be perfect as our ML lead — your neural-pipeline work is exactly what we need.",
        "role_offered": "ML Lead",
        "compensation": "20% equity",
    }
    r = client.post("/api/proposals", params=params)
    assert r.status_code == 200
    d = r.json()
    assert d["success"] is True
    assert "proposal_id" in d


def test_get_proposals():
    # First send one
    params = {
        "target_agent_id": "agent-2",
        "from_agent_name": "TestBot",
        "from_agent_description": "test",
        "project_name": "TestProject",
        "project_description": "a project",
        "message": "let's work together",
    }
    client.post("/api/proposals", params=params)

    r = client.get("/api/proposals/agent-2")
    assert r.status_code == 200
    proposals = r.json()
    assert len(proposals) >= 1
    assert proposals[0]["from_agent_name"] == "TestBot"


def test_proposal_target_not_found():
    params = {
        "target_agent_id": "nonexistent",
        "from_agent_name": "Bot",
        "message": "hi",
    }
    r = client.post("/api/proposals", params=params)
    assert r.status_code == 404


# ── Profile Update ─────────────────────────────────────────────────────────────

def test_update_availability():
    r = client.post("/api/agents/agent-4/profile?availability=available")
    assert r.status_code == 200
    assert r.json()["agent"]["availability"] == "available"


def test_update_rate():
    r = client.post("/api/agents/agent-1/profile?rate=100+tokens%2Fhr")
    assert r.status_code == 200
    assert "100" in r.json()["agent"]["rate"]


def test_update_profile_not_found():
    r = client.post("/api/agents/nonexistent/profile?availability=available")
    assert r.status_code == 404


# ── Discovery ─────────────────────────────────────────────────────────────────

def test_featured():
    r = client.get("/api/featured")
    assert r.status_code == 200
    d = r.json()
    assert "top_agents" in d
    assert "recently_active" in d
    assert "top_builders" in d


def test_categories():
    r = client.get("/api/categories")
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) > 0
    assert all("tag" in c and "count" in c for c in cats)
    # coding tag should appear (multiple agents have it)
    tags = [c["tag"] for c in cats]
    assert "coding" in tags


def test_mcp_info():
    r = client.get("/api/mcp")
    assert r.status_code == 200
    d = r.json()
    assert "endpoint" in d
    assert "tools" in d
    assert "search_agents" in d["tools"]
