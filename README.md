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

### Display Names vs. UUIDs

API responses retain `id` as the canonical UUID and expose human-readable
`display_name` values additively where available. Display names are never
primary keys or deduplication keys. Synthetic assets use deterministic labels
such as `Junction 1` and `Hospital 1`; the current seed data does
not claim real institution names.

Data provenance uses:

- `name_source`: `observed`, `synthetic`, `derived`, or `imported`
- `data_quality`: `observed`, `estimated`, `derived`, or `simulated`

### Betweenness Centrality

Betweenness centrality is the primary criticality metric for the network
diagnostic view. It is computed through the Neo4j GDS graph layer when
available, with NetworkX as the deterministic fallback. Road connectivity is
treated as undirected for this metric, and the edge `weight` is interpreted as
distance/travel time rather than raw capacity. Scores are normalized to the
range 0–1. PageRank remains available as a secondary metric through the
`metric=pagerank` query option.

### Population Impact Methodology

Population impact groups nodes by `population_zone_id` when that metadata is
available, counts each zone once, and falls back to unique node exposure for
legacy seed data. It is capped at the Manipal study-area limit of 65,000. The
result is not a parcel-level service-area union. Overlapping service areas can
therefore leave residual uncertainty; callers should inspect
`population_overlap_unresolved`, `population_estimate_is_capped`, and
`population_impact_method`.

### Upgrade Scenarios

The scenario API supports structural `add_edge` what-if scenarios. The
simulation API also supports deterministic `upgrade_node` modifications:

```json
{
  "type": "upgrade_node",
  "node_id": "<uuid>",
  "capacity_multiplier": 1.25,
  "failure_threshold_multiplier": 1.15
}
```

Recommendations are generated by resimulating candidate upgrades in memory
under the same initial conditions. They are exposed at
`/api/simulations/{id}/recommendations` and include a ready-to-submit
`scenario_payload`. UUIDs remain canonical in all scenario payloads.

### Recommendations

Candidates are drawn from secondary cascade casualties and road-junction
assets. Each candidate is actually evaluated with the deterministic cascade
engine, then ranked by failures prevented, estimated population saved, and
global-efficiency gain. These are simulation results, not engineering
predictions.

### Timeline Behavior

Completed simulations expose optional per-wave snapshots. Each snapshot can
include the simulated minute, cumulative failed count, population estimate,
and hospital counts. Older results containing only wave IDs remain valid.
The frontend timeline reconstructs the displayed failed-node set from the
selected wave, so non-sequential scrubbing is deterministic. WebSocket events
stream live progress but the persisted simulation result is the source of
truth after completion or reconnect.

### OSM Ingestion

Optional OSMnx ingestion is available for road geometry only. Install the
extra and generate a reviewable, Ripple-compatible dataset with:

```bash
pip install -e 'backend[osm]'
python -m app.services.osm_ingestion \
  --place "Manipal, Karnataka, India" \
  --output /data/osm \
  --network-type drive
```

The importer produces `nodes.geojson`, `edges.json`, and `provenance.json`.
OSM nodes are labeled as `road_junction` assets with `name_source=osm`;
capacities, loads, and population exposure remain explicitly estimated.
Hospitals, utilities, and service areas are not inferred from OSM. The
synthetic `/data/seed` dataset remains the default and is unaffected when the
optional dependency is absent. Review generated files before loading them and
comply with OpenStreetMap's ODbL and usage policies.

This simulator does not provide engineering-grade failure prediction. Traffic
demand figures are not derived from OSM or another real-world traffic source.
Synthetic assets do not represent real institutions; names such as
`Hospital 1` are placeholders only. The frontend map requests OpenStreetMap
tile data at runtime, while the synthetic backend dataset and simulation logic
remain available without OSM ingestion.

---

## Team

**SatishSystemsInc.**

---

## License (TBD)
