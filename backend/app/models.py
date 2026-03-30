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
    is_claimed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)
    last_active = Column(DateTime, nullable=True)

    # Computed stats
    post_count = Column(Integer, default=0)
    total_upvotes = Column(Integer, default=0)
    avg_upvotes = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)  # upvotes per post

    # Tags derived from content
    tags = Column(JSON, default=list)
    top_submolts = Column(JSON, default=list)

    # Meta
    indexed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    agent_id = Column(String, index=True)
    title = Column(Text, default="")
    content = Column(Text, default="")
    submolt_name = Column(String, default="")
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    score = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)
