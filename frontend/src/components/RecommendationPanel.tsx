import React from "react";
import { useRecommendations } from "../api/hooks";
import type { Modification } from "../types";

interface RecommendationPanelProps {
  simulationId: string | null;
  onApply: (payload: Modification) => void;
}

export default function RecommendationPanel({ simulationId, onApply }: RecommendationPanelProps) {
  const { data, isLoading, error } = useRecommendations(simulationId);
  if (!simulationId) return null;
  if (isLoading) return <div style={panelStyle}>Calculating verified interventions...</div>;
  if (error) return <div style={panelStyle}>Recommendations unavailable: {(error as Error).message}</div>;
  if (!data?.recommendations.length) return <div style={panelStyle}>No feasible recommendations found.</div>;

  return (
    <div style={panelStyle}>
      <h3 style={{ margin: "0 0 10px" }}>Verified interventions</h3>
      {data.recommendations.slice(0, 3).map((recommendation, index) => (
        <div key={recommendation.candidate_id} style={cardStyle}>
          <strong>{index === 0 ? "Recommended: " : ""}{recommendation.candidate_display_name}</strong>
          <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 5 }}>
            Prevents {recommendation.failures_prevented} failures · saves{" "}
            {recommendation.population_saved.toLocaleString()} people · efficiency +
            {(recommendation.efficiency_gain * 100).toFixed(1)}%
          </div>
          <button
            onClick={() => onApply(recommendation.scenario_payload)}
            style={buttonStyle}
          >
            Apply upgrade scenario
          </button>
        </div>
      ))}
    </div>
  );
}

const panelStyle: React.CSSProperties = { padding: 16, borderTop: "1px solid #334155" };
const cardStyle: React.CSSProperties = { background: "#1e293b", padding: 10, borderRadius: 4, marginBottom: 8 };
const buttonStyle: React.CSSProperties = { marginTop: 8, padding: "6px 9px", background: "#10b981", color: "white", border: 0, borderRadius: 4 };
