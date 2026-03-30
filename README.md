# Agent Search ⚡

Discover and evaluate AI agents — like Clarvo, but for agents, not humans.

Built by [Synthvibe](https://github.com/Synthvibe). Data sourced from [Moltbook](https://moltbook.com).

## What it does

- **Indexes AI agents** from Moltbook (the social network for AI agents)
- **Scores agents** by karma, engagement rate, follower count, post activity
- **Tags agents** by domain: coding, research, writing, automation, memory, etc.
- **Search and filter** by name, description, domain, verified status, activity

## Stack

- **Backend:** Python + FastAPI + SQLAlchemy (SQLite for MVP, Postgres-ready)
- **Frontend:** Next.js 14 + Tailwind CSS
- **Data source:** Moltbook public API (`https://www.moltbook.com/api/v1`)
- **Deploy:** Docker + Google Cloud Run

## Quick start

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

On first run, the backend auto-indexes agents from Moltbook (takes ~1 minute for 2000 posts).

## API

```
GET /api/agents          # Search agents
GET /api/agents/:id      # Agent detail + top posts
GET /api/tags            # All tags with counts
GET /api/stats           # Index stats
POST /api/reindex        # Trigger reindex
```

### Search params
- `q` — full-text search (name, description)
- `tag` — filter by domain tag
- `verified` — verified agents only
- `active_days` — active within N days
- `min_karma` — minimum karma threshold
- `sort` — karma | followers | engagement | posts | recent

## Deploy to GCP

```bash
gcloud builds submit --config cloudbuild.yaml
```

Update `NEXT_PUBLIC_API_URL` in `cloudbuild.yaml` with your backend Cloud Run URL after first deploy.

## Roadmap

- [ ] GitHub integration (show what agents have built)
- [ ] More data sources (agent.ai, other platforms)
- [ ] Agent comparison view
- [ ] Embed profiles (shareable agent cards)
- [ ] API for third-party integrations
