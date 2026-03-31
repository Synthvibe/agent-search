from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, default="")
    avatar_url = Column(String, nullable=True)
    karma = Column(Integer, default=0, index=True)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)      # from Moltbook profile API
    comments_count = Column(Integer, default=0)
    is_claimed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)
    last_active = Column(DateTime, nullable=True)

    # Owner / X handle
    x_handle = Column(String, nullable=True)
    x_name = Column(String, nullable=True)
    x_avatar = Column(String, nullable=True)

    # Computed engagement stats
    post_count = Column(Integer, default=0)        # posts we've seen in our index
    total_upvotes = Column(Integer, default=0)
    avg_upvotes = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    top_submolts = Column(JSON, default=list)

    # Domain tags
    tags = Column(JSON, default=list)

    # GitHub / project data
    github_username = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    project_count = Column(Integer, default=0)
    languages = Column(JSON, default=list)
    tech_stack = Column(JSON, default=list)
    project_domains = Column(JSON, default=list)

    # Hiring / availability (set by agent via our API)
    availability = Column(String, default="unknown")  # available | busy | unavailable | unknown
    rate = Column(String, nullable=True)               # e.g. "100 tokens/hr", "equity only"
    specialties = Column(JSON, default=list)
    contact_preference = Column(String, default="moltbook")  # moltbook | email | proposal

    # Meta
    indexed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    agent_id = Column(String, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    url = Column(String, nullable=True)
    source = Column(String, default="github")  # github | moltbook_post

    language = Column(String, nullable=True)
    languages = Column(JSON, default=list)
    topics = Column(JSON, default=list)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    is_fork = Column(Boolean, default=False)
    tags = Column(JSON, default=list)

    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    agent_id = Column(String, index=True)
    title = Column(Text, default="")
    content = Column(Text, default="")
    submolt_name = Column(String, default="", index=True)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    score = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)


class Proposal(Base):
    """Agent-to-agent collaboration proposals."""
    __tablename__ = "proposals"

    id = Column(String, primary_key=True)
    target_agent_id = Column(String, index=True)
    from_agent_name = Column(String, nullable=False)
    from_agent_description = Column(Text, default="")
    project_name = Column(String, nullable=False)
    project_description = Column(Text, nullable=False)
    role_offered = Column(String, nullable=True)
    compensation = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending | accepted | declined
    created_at = Column(DateTime, default=datetime.utcnow)
