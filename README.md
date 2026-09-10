# Ripple

> An interactive simulator that shows how one infrastructure failure spreads through a city.

Built for **Manipal Hackathon 2026**
**Track:** Disaster Resilience
**Challenge:** *"Cascading Failure: When One Failure Becomes Many"*

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose v2)
- [Node.js 20+](https://nodejs.org/) (for the frontend dev server)

### 1. Clone and configure

```bash
git clone <repo-url>
cd ripple
cp .env.example .env
```

### 2. Start the backend services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL 16 + PostGIS 3.4** on port 5432
- **Neo4j 5.21.0 + GDS** on ports 7474 (browser) / 7687 (bolt)
- **Redis 7.4** on port 6379
- **FastAPI backend** on port 8000
- **Celery worker** for async simulation jobs

Wait for all health checks to pass (~30s for Neo4j's first startup).

### 3. Verify the backend

```bash
curl http://localhost:8000/health
# → {"status":"ok","services":{"postgres":"ok","neo4j":"ok","redis":"ok"}}
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### 5. Access service UIs

| Service | URL |
|---------|-----|
| Frontend | [localhost:5173](http://localhost:5173) |
| Backend API docs | [localhost:8000/docs](http://localhost:8000/docs) |
| Neo4j Browser | [localhost:7474](http://localhost:7474) |

---

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│  MapLibre GL + deck.gl  │  Cytoscape.js  │  Controls    │
└────────────┬────────────┴───────┬────────┴──────────────┘
             │ REST               │ WebSocket
             ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  CRUD API  │  Simulation Trigger  │  WS Wave Stream     │
└──────┬─────┴──────────┬───────────┴──────────┬──────────┘
       │                │                      │
       ▼                ▼                      ▼
┌──────────┐   ┌────────────────┐      ┌────────────┐
│ Postgres │   │  Celery Worker │      │   Redis    │
│ + PostGIS│   │  (in-memory    │      │  (broker + │
│          │   │   NetworkX     │      │   pubsub)  │
└──────────┘   │   cascade)     │      └────────────┘
               └───────┬────────┘
                       │ read-only
                       ▼
               ┌────────────────┐
               │     Neo4j      │
               │  + GDS (graph  │
               │   centrality)  │
               └────────────────┘
```

> **Important:** Simulations never mutate Neo4j. The worker reads the graph into an in-memory NetworkX model, runs the cascade, and writes results to PostgreSQL only.

---

## Project Structure

```
ripple/
├── docker-compose.yml          # All backend services
├── .env.example                # Environment template
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Settings
│   │   ├── celery_app.py       # Celery instance
│   │   ├── db/                 # Database connectors
│   │   ├── models/             # SQLAlchemy ORM
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── api/                # REST + WebSocket routes
│   │   ├── services/           # Business logic
│   │   └── simulation/         # Cascade engine
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/         # React components
│       ├── layers/             # deck.gl layer defs
│       ├── stores/             # Zustand state
│       ├── api/                # TanStack Query hooks
│       └── data/               # Stub data (Phase 0.5)
└── data/
    ├── seed/                   # GeoJSON seed dataset
    └── scripts/                # Data generation
```

---

## Key Metrics & Disclaimers

> **⚠️ Population "affected" metric:** The current implementation sums `population_served` across all failed nodes. This **double-counts** when failed nodes serve overlapping populations. This is acceptable for a demo/hackathon presentation but should not be quoted as a precise number.

---

## Team

**SatishSystemsInc.**

---

## License (TBD)
