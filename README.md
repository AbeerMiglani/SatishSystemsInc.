# Ripple

> An interactive simulator that shows how one infrastructure failure spreads through a city.

Built for **Manipal Hackathon 2026**
**Track:** Disaster Resilience
**Challenge:** *“Cascading Failure: When One Failure Becomes Many”*

---

## Overview

Cities run on interconnected systems.

Power feeds water pumps. Water and electricity keep hospitals running. Roads connect critical facilities. When one part of this network fails, the consequences can spread far beyond the original failure.

Most infrastructure monitoring tools look at individual systems in isolation. **Ripple** treats the city as one interconnected network, allowing users to visualize and understand how a single failure can cascade through multiple dependent services.

With Ripple, you can:

* Fail any infrastructure node with a click
* Visualize how the failure propagates through the network
* Estimate how many services and people are affected
* Identify the infrastructure assets that are most critical
* Test potential fixes and compare outcomes
* Understand cascading failures through an interactive simulation

---

## What It Does

Ripple models a city as a **dependency graph**.

Each infrastructure asset is represented as a node, while connections between nodes represent dependencies.

For example:

```text
Power Substation
       |
       v
Water Pump ------> Water Treatment
       |
       v
    Hospital
```

If the power substation fails, the water pump may stop working. This can affect the water treatment system, which can then impact the hospital.

Ripple simulates this chain reaction and shows how far the original failure can spread.

---

## How It Works

### 1. City as a Graph

The city is represented as a graph:

* **Nodes** — infrastructure assets
* **Edges** — dependencies between assets

Example node types include:

* Power substations
* Water stations
* Hospitals
* Roads
* Critical facilities

---

### 2. Failure Propagation

When a user fails a node, Ripple traverses the dependency graph outward.

A dependent node fails when it loses the support required to keep operating.

The simulation follows a cascading process:

```text
Initial Failure
      |
      v
Direct Dependencies
      |
      v
Secondary Dependencies
      |
      v
Tertiary Dependencies
      |
      v
Cascading Failure
```

The simulation continues until no additional infrastructure assets are affected.

---

### 3. Impact Calculation

Ripple tracks the impact of each scenario, including:

* Number of failed infrastructure assets
* Number of affected services
* Approximate population affected
* Overall extent of the cascading failure

This makes it possible to compare different failure scenarios.

---

### 4. Identifying Critical Assets

Ripple can simulate the failure of each infrastructure node individually and measure how many other assets are affected.

This allows the system to rank infrastructure based on its potential failure impact and identify critical weak points in the network.

For example:

```text
Most Critical
     |
     v
Power Substation A
Water Station B
Hospital C
Road Junction D
     |
     v
Least Critical
```

High-impact assets represent infrastructure that may require additional protection, redundancy, or monitoring.

---

### 5. Testing Fixes

Ripple allows users to test potential interventions.

A user can modify the network, introduce additional support or redundancy, and run the same scenario again.

The results can then be compared:

```text
WITHOUT FIX

Failure
   |
   v
Water
   |
   v
Hospital
   |
   v
Emergency Services

High Impact
```

```text
WITH FIX

Failure
   |
   v
Backup Supply
   |
   v
Water
   |
   v
Hospital

Reduced Impact
```

This demonstrates how resilience measures can reduce cascading failures.

---

## Key Features

| Feature               | Description                                                 |
| --------------------- | ----------------------------------------------------------- |
| Interactive Graph     | Explore the city's infrastructure dependency network        |
| Failure Simulation    | Click a node to trigger a failure                           |
| Cascade Visualization | Watch the failure spread through dependent systems          |
| Impact Estimation     | Track services and approximate population affected          |
| Criticality Ranking   | Identify infrastructure with the highest failure impact     |
| Intervention Testing  | Add or test fixes and compare scenarios                     |
| Optional Map Layer    | Visualize infrastructure geographically                     |
| Scenario Summaries    | Generate short, readable explanations of simulation results |

---

## Architecture

```text
                    +------------------+
                    |    React UI      |
                    |                  |
                    |  Graph / Map     |
                    +--------+---------+
                             |
                             | API
                             v
                    +------------------+
                    |    Backend       |
                    |                  |
                    | Network +        |
                    | Simulation API   |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Graph Simulation |
                    |                  |
                    | Traversal        |
                    | Centrality       |
                    | Impact Analysis  |
                    +------------------+
```

---

## Tech Stack (TBD)

### Frontend

* React
* Cytoscape.js for interactive graph visualization
* Optional map layer for geographic visualization

### Backend

A simple API responsible for:

* Storing the infrastructure network
* Running simulations
* Processing failure propagation
* Returning simulation and impact results

### Graph Logic

Ripple uses standard graph algorithms, including:

* Graph traversal
* Dependency propagation
* Centrality analysis
* Impact ranking

---

## Project Structure

> Update this section once the final project structure is finalized.

```text
ripple/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── src/
│   └── ...
│
├── data/
│   └── sample-network/
│
├── README.md
└── ...
```

---

## Running the Project

> Setup instructions will be added once the project is fully configured.

```bash
# Clone the repository

# Install dependencies

# Start the backend

# Start the frontend
```

---

## Data

The sample network is **hand-built to represent a small city**.

It is not based on real infrastructure data. The dataset is designed specifically to demonstrate how Ripple's cascading-failure simulation works.

---

## Use Case

Ripple is designed as a demonstration and decision-support concept for disaster resilience.

Potential applications include:

* Identifying critical infrastructure
* Understanding infrastructure dependencies
* Evaluating cascading failure risks
* Testing redundancy and resilience strategies
* Supporting disaster preparedness planning
* Communicating complex infrastructure risks visually

---

## Future Improvements

Potential future improvements include:

* Real-world infrastructure datasets
* More detailed dependency rules
* Probabilistic failure models
* Real-time infrastructure data
* Advanced geographic visualization
* More sophisticated population-impact estimation
* Multiple simultaneous failures
* Recovery and restoration simulations
* Automated resilience recommendations

---

## Team

**SatishSystemsInc.**

---

## License (TBD)
