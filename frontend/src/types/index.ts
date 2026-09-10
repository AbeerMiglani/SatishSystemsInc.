/**
 * Shared TypeScript types for the Ripple frontend.
 */

// ---------------------------------------------------------------------------
// Node types
// ---------------------------------------------------------------------------
export type NodeType =
  | "power_substation"
  | "water_station"
  | "hospital"
  | "road_junction"
  | "telecom_tower";

export type NodeStatus = "operational" | "degraded" | "failed";

export interface InfraNode {
  id: string;
  name: string;
  node_type: NodeType;
  lat: number;
  lng: number;
  capacity: number;
  current_load: number;
  failure_threshold: number;
  population_served: number;
  status: NodeStatus;
}

// ---------------------------------------------------------------------------
// Edge types
// ---------------------------------------------------------------------------
export type EdgeType = "power_supply" | "water_supply" | "road_link" | "depends_on";

export interface InfraEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: EdgeType;
  weight: number;
  capacity: number;
  is_bidirectional: boolean;
}

// ---------------------------------------------------------------------------
// Network
// ---------------------------------------------------------------------------
export interface Network {
  id: string;
  name: string;
  nodes: InfraNode[];
  edges: InfraEdge[];
}

// ---------------------------------------------------------------------------
// Simulation
// ---------------------------------------------------------------------------
export interface CascadeWave {
  wave: number;
  failed_node_ids: string[];
}

export interface SimulationResult {
  id: string;
  network_id: string;
  initial_failures: string[];
  waves: CascadeWave[];
  total_failed: number;
  population_affected_estimate: number;
  global_efficiency_before: number;
  global_efficiency_after: number;
  status: "pending" | "running" | "completed" | "failed";
}

export interface CentralityScore {
  node_id: string;
  score: number;
  rank: number;
}

// ---------------------------------------------------------------------------
// Scenario
// ---------------------------------------------------------------------------
export interface Modification {
  action: "add_edge" | "remove_edge" | "add_node" | "remove_node" | "update_node";
  target_id: string;
  data: Record<string, unknown>;
}

export interface Scenario {
  id: string;
  network_id: string;
  name: string;
  description: string;
  modifications: Modification[];
  initial_failures: string[];
  cached_result_id: string | null;
}

// ---------------------------------------------------------------------------
// UI color mapping
// ---------------------------------------------------------------------------
export const NODE_COLORS: Record<NodeType, [number, number, number]> = {
  power_substation: [239, 68, 68],   // red
  water_station: [59, 130, 246],     // blue
  hospital: [34, 197, 94],           // green
  road_junction: [148, 163, 184],    // slate gray
  telecom_tower: [234, 179, 8],      // yellow
};

export const NODE_LABELS: Record<NodeType, string> = {
  power_substation: "Power",
  water_station: "Water",
  hospital: "Hospital",
  road_junction: "Road",
  telecom_tower: "Telecom",
};

export const FAILED_COLOR: [number, number, number] = [220, 38, 38]; // bright red
export const SELECTED_COLOR: [number, number, number] = [251, 191, 36]; // amber
