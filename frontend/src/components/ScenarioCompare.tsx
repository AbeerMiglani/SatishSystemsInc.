import React, { useState } from "react";
import { useCompareScenarios } from "../api/hooks";
import { useSimulationStore } from "../stores/simulationStore";

const ScenarioCompare: React.FC = () => {
  // Ideally these IDs would be selected from a list, but for demo purposes, 
  // we just assume the user has a baseline and a scenario in mind.
  const [baselineId, setBaselineId] = useState<string>("");
  const [scenarioId, setScenarioId] = useState<string>("");
  
  const { data, isLoading, error } = useCompareScenarios(
    baselineId.length > 30 ? baselineId : null, 
    scenarioId.length > 30 ? scenarioId : null
  );

  return (
    <div style={{ padding: 16, background: "#1e293b", borderTop: "1px solid #334155" }}>
      <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>Scenario Comparison</h3>
      
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
        <input 
          type="text" 
          placeholder="Baseline Simulation ID" 
          value={baselineId}
          onChange={(e) => setBaselineId(e.target.value)}
          style={{ padding: "6px", background: "#0f172a", border: "1px solid #475569", color: "white", borderRadius: 4 }}
        />
        <input 
          type="text" 
          placeholder="Scenario ID" 
          value={scenarioId}
          onChange={(e) => setScenarioId(e.target.value)}
          style={{ padding: "6px", background: "#0f172a", border: "1px solid #475569", color: "white", borderRadius: 4 }}
        />
      </div>

      {isLoading && <p>Loading comparison...</p>}
      {error && <p style={{ color: "#ef4444" }}>{(error as Error).message}</p>}
      
      {data && (
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ flex: 1, padding: 12, background: "#0f172a", borderRadius: 4 }}>
            <h4 style={{ margin: "0 0 8px 0", color: "#94a3b8" }}>Baseline</h4>
            <p>Failed: {data.baseline_result.total_failed}</p>
            <p>Pop Affected: {data.baseline_result.population_affected_estimate.toLocaleString()}</p>
            <p>Waves: {data.baseline_result.waves.length}</p>
            <p>Final Eff: {(data.baseline_result.global_efficiency_after! * 100).toFixed(1)}%</p>
          </div>
          <div style={{ flex: 1, padding: 12, background: "#064e3b", borderRadius: 4 }}>
            <h4 style={{ margin: "0 0 8px 0", color: "#a7f3d0" }}>What-If Scenario</h4>
            <p>Failed: {data.scenario_result.total_failed}</p>
            <p>Pop Affected: {data.scenario_result.population_affected_estimate.toLocaleString()}</p>
            <p>Waves: {data.scenario_result.waves.length}</p>
            <p>Final Eff: {(data.scenario_result.global_efficiency_after! * 100).toFixed(1)}%</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScenarioCompare;
