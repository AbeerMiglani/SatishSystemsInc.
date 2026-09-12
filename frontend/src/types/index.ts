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
  display_name?: string;
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
  simulated_minute?: number;
  failed_node_ids: string[];
  cumulative_failed_count?: number;
  population_affected_estimate?: number;
  hospital_count_operational?: number;
  hospital_count_failed?: number;
}

export interface SimulationResult {
  id: string;
  network_id: string;
  initial_failures: string[];
  waves: CascadeWave[];
  total_failed: number;
  population_affected_estimate: number;
  population_total?: number;
  population_affected_percentage?: number;
  population_overlap_unresolved?: boolean;
  population_estimate_is_capped?: boolean;
  population_impact_method?: string;
  global_efficiency_before: number;
  global_efficiency_after: number;
  status: "pending" | "running" | "completed" | "failed";
}

export interface Recommendation {
  candidate_id: string;
  candidate_display_name: string;
  scenario_payload: Modification;
  failures_prevented: number;
  population_saved: number;
  efficiency_gain: number;
  verified: boolean;
}

export interface CentralityScore {
  node_id: string;
  display_name?: string;
  metric?: "betweenness" | "pagerank";
  score: number;
  rank: number;
}

// ---------------------------------------------------------------------------
// Scenario
// ---------------------------------------------------------------------------
export interface Modification {
  type: "add_edge" | "upgrade_node";
  source?: string;
  target?: string;
  node_id?: string;
  edge_type?: EdgeType;
  weight?: number;
  capacity?: number;
  capacity_multiplier?: number;
  capacity_add?: number;
  failure_threshold?: number;
  failure_threshold_multiplier?: number;
  failure_threshold_add?: number;
  is_bidirectional?: boolean;
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
