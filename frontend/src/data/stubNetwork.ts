/**
 * Hardcoded stub network for Phase 0.5 walking skeleton.
 *
 * 8 nodes placed at real Manipal, India coordinates:
 *   - 2 power substations
 *   - 1 water station
 *   - 1 hospital
 *   - 3 road junctions
 *   - 1 telecom tower
 *
 * This is replaced with real API data starting Phase 2.
 */

import type {
  InfraNode,
  InfraEdge,
  Network,
  CascadeWave,
} from "../types";

// ---------------------------------------------------------------------------
// Nodes — centered around Manipal, India (~13.35°N, 74.79°E)
// ---------------------------------------------------------------------------
const nodes: InfraNode[] = [
  {
    id: "ps-1",
    name: "Manipal Main Substation",
    node_type: "power_substation",
    lat: 13.3525,
    lng: 74.7870,
    capacity: 100,
    current_load: 78,
    failure_threshold: 1.0,
    population_served: 25000,
    status: "operational",
  },
  {
    id: "ps-2",
    name: "Tiger Circle Substation",
    node_type: "power_substation",
    lat: 13.3440,
    lng: 74.7935,
    capacity: 80,
    current_load: 55,
    failure_threshold: 1.0,
    population_served: 15000,
    status: "operational",
  },
  {
    id: "ws-1",
    name: "Manipal Water Pumping Station",
    node_type: "water_station",
    lat: 13.3480,
    lng: 74.7820,
    capacity: 60,
    current_load: 45,
    failure_threshold: 1.0,
    population_served: 30000,
    status: "operational",
  },
  {
    id: "hp-1",
    name: "Kasturba Hospital",
    node_type: "hospital",
    lat: 13.3505,
    lng: 74.7910,
    capacity: 50,
    current_load: 35,
    failure_threshold: 1.0,
    population_served: 40000,
    status: "operational",
  },
  {
    id: "rj-1",
    name: "Manipal Junction",
    node_type: "road_junction",
    lat: 13.3510,
    lng: 74.7885,
    capacity: 90,
    current_load: 70,
    failure_threshold: 1.0,
    population_served: 5000,
    status: "operational",
  },
  {
    id: "rj-2",
    name: "End Point Road",
    node_type: "road_junction",
    lat: 13.3465,
    lng: 74.7890,
    capacity: 70,
    current_load: 50,
    failure_threshold: 1.0,
    population_served: 3000,
    status: "operational",
  },
  {
    id: "rj-3",
    name: "Eshwar Nagar Junction",
    node_type: "road_junction",
    lat: 13.3545,
    lng: 74.7840,
    capacity: 60,
    current_load: 40,
    failure_threshold: 1.0,
    population_served: 4000,
    status: "operational",
  },
  {
    id: "tc-1",
    name: "Manipal Telecom Tower",
    node_type: "telecom_tower",
    lat: 13.3490,
    lng: 74.7960,
    capacity: 40,
    current_load: 28,
    failure_threshold: 1.0,
    population_served: 20000,
    status: "operational",
  },
];

// ---------------------------------------------------------------------------
// Edges
// ---------------------------------------------------------------------------
const edges: InfraEdge[] = [
  // Power feeds
  {
    id: "e-1",
    source_id: "ps-1",
    target_id: "ws-1",
    edge_type: "power_supply",
    weight: 1.0,
    capacity: 50,
    is_bidirectional: false,
  },
  {
    id: "e-2",
    source_id: "ps-1",
    target_id: "rj-1",
    edge_type: "power_supply",
    weight: 1.0,
    capacity: 40,
    is_bidirectional: false,
  },
  {
    id: "e-3",
    source_id: "ps-2",
    target_id: "hp-1",
    edge_type: "power_supply",
    weight: 1.0,
    capacity: 45,
    is_bidirectional: false,
  },
  {
    id: "e-4",
    source_id: "ps-2",
    target_id: "tc-1",
    edge_type: "power_supply",
    weight: 1.0,
    capacity: 30,
    is_bidirectional: false,
  },
  // Water feed
  {
    id: "e-5",
    source_id: "ws-1",
    target_id: "hp-1",
    edge_type: "water_supply",
    weight: 1.0,
    capacity: 35,
    is_bidirectional: false,
  },
  // Road links (bidirectional)
  {
    id: "e-6",
    source_id: "rj-1",
    target_id: "rj-2",
    edge_type: "road_link",
    weight: 1.2,
    capacity: 60,
    is_bidirectional: true,
  },
  {
    id: "e-7",
    source_id: "rj-1",
    target_id: "rj-3",
    edge_type: "road_link",
    weight: 0.8,
    capacity: 50,
    is_bidirectional: true,
  },
  {
    id: "e-8",
    source_id: "rj-2",
    target_id: "hp-1",
    edge_type: "road_link",
    weight: 1.5,
    capacity: 40,
    is_bidirectional: true,
  },
  {
    id: "e-9",
    source_id: "rj-3",
    target_id: "ps-1",
    edge_type: "road_link",
    weight: 0.6,
    capacity: 45,
    is_bidirectional: true,
  },
  // Dependency
  {
    id: "e-10",
    source_id: "hp-1",
    target_id: "tc-1",
    edge_type: "depends_on",
    weight: 1.0,
    capacity: 20,
    is_bidirectional: false,
  },
];

// ---------------------------------------------------------------------------
// Assembled network
// ---------------------------------------------------------------------------
export const STUB_NETWORK: Network = {
  id: "stub-network-1",
  name: "Manipal Demo Network",
  nodes,
  edges,
};

// ---------------------------------------------------------------------------
// Stub cascade response for "Manipal Main Substation" (ps-1) failure
// ---------------------------------------------------------------------------
// Wave 0: ps-1 fails (user-triggered)
// Wave 1: ws-1 loses power → fails; rj-1 overloaded → fails
// Wave 2: hp-1 loses water (ws-1 gone) → fails
// Wave 3: tc-1 depends on hp-1 → fails
export const STUB_CASCADE: Record<string, CascadeWave[]> = {
  "ps-1": [
    { wave: 0, failed_node_ids: ["ps-1"] },
    { wave: 1, failed_node_ids: ["ws-1", "rj-1"] },
    { wave: 2, failed_node_ids: ["hp-1"] },
    { wave: 3, failed_node_ids: ["tc-1"] },
  ],
  "ps-2": [
    { wave: 0, failed_node_ids: ["ps-2"] },
    { wave: 1, failed_node_ids: ["hp-1", "tc-1"] },
  ],
  // Default fallback for any other node
  _default: [
    { wave: 0, failed_node_ids: [] }, // placeholder; replaced at runtime
  ],
};

/**
 * Get stub cascade waves for a given node ID.
 * Falls back to a single-wave (just the clicked node) if no pre-computed cascade exists.
 */
export function getStubCascade(nodeId: string): CascadeWave[] {
  if (STUB_CASCADE[nodeId]) {
    return STUB_CASCADE[nodeId];
  }
  return [{ wave: 0, failed_node_ids: [nodeId] }];
}
