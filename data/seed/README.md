# Ripple seed data

The seed files describe a deterministic synthetic infrastructure network
positioned at real Manipal, India coordinates. The coordinates make the demo
meaningful on the map; the assets, capacities, loads, population values, and
traffic-like relationships are synthetic estimates.

## Contents

- `nodes.geojson` — 120 infrastructure nodes:
  - 100 road junctions
  - 8 power substations
  - 6 water stations
  - 4 hospitals
  - 2 telecom towers
- `edges.json` — directed dependency links and bidirectional road links.

## Naming and data limits

Names are generated deterministically with zero-padded numbering, for example
`Junction 001`, `Hospital 01`, and `Substation 01`. They are synthetic labels,
not real institution or road names. The dataset does not provide exact
population figures, observed traffic demand, or engineering failure data.

## Regeneration

From the repository root:

```bash
python data/scripts/generate_synthetic.py
```

The generator uses a fixed seed and validates graph connectivity and hospital
reachability before writing the files.

## Optional OSM road data

The backend includes an opt-in OSMnx exporter for road geometry. It writes a
separate dataset and never replaces these deterministic fixtures automatically:

```bash
pip install -e 'backend[osm]'
python -m app.services.osm_ingestion --place "Manipal, Karnataka, India" --output /data/osm
```

The OSM output contains road junctions and road links only. Operational
capacities and population exposure are estimates and must not be presented as
official infrastructure data.
