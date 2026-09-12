import React, { useEffect, useState } from "react";
import { useUIStore } from "../stores/uiStore";
import { useSimulationStore } from "../stores/simulationStore";
import { useRunSimulation, useSimulationResult, useCreateScenario } from "../api/hooks";
import CascadeTimeline from "./CascadeTimeline";
import RecommendationPanel from "./RecommendationPanel";
import type { Modification } from "../types";

const ControlPanel: React.FC = () => {
  const mode = useUIStore((s) => s.mode);
  const setMode = useUIStore((s) => s.setMode);
  const networkId = useUIStore((s) => s.networkId);
  const selectedNodeIds = useUIStore((s) => s.selectedNodeIds);
  const redundancyNodes = useUIStore((s) => s.redundancyNodes);
  const clearSelection = useUIStore((s) => s.clearSelection);
  const clearRedundancyNodes = useUIStore((s) => s.clearRedundancyNodes);

  const { result, currentWave, isPlaying, play, pause, reset, setWave, setSimulationResult } = useSimulationStore();
  const [dismissedSimulationIds, setDismissedSimulationIds] = useState<Set<string>>(new Set());
  
  const simMutation = useRunSimulation();
  const createScenarioMutation = useCreateScenario();
  
  const { data: polledResult } = useSimulationResult(simMutation.data?.id || null);

  useEffect(() => {
    if (polledResult && polledResult.status === "completed") {
      if (!dismissedSimulationIds.has(polledResult.id) && (!result || result.id !== polledResult.id)) {
        setSimulationResult(polledResult);
      }
    }
  }, [polledResult, result, dismissedSimulationIds, setSimulationResult]);

  const handleRunBaseline = () => {
    if (!networkId || selectedNodeIds.size === 0) return;
    simMutation.mutate({
      network_id: networkId,
      initial_failures: Array.from(selectedNodeIds),
      scenario_id: undefined
    });
  };

  const handleSaveScenario = async () => {
    if (!networkId || redundancyNodes.length !== 2 || selectedNodeIds.size === 0) return;
    try {
      const scenario = await createScenarioMutation.mutateAsync({
        network_id: networkId,
        name: "Redundancy What-If",
        modifications: [
          {
            type: "add_edge",
            source: redundancyNodes[0],
            target: redundancyNodes[1],
            edge_type: "power_supply",
            is_bidirectional: true
          }
        ],
        initial_failures: Array.from(selectedNodeIds)
      });
      
      // Run the scenario simulation
      simMutation.mutate({
        network_id: networkId,
        initial_failures: Array.from(selectedNodeIds),
        scenario_id: scenario.id
      });
      
      setMode("default");
    } catch (e) {
      console.error(e);
      alert("Failed to create scenario: " + e);
    }
  };

  const handleApplyRecommendation = async (payload: Modification) => {
    if (!result || result.status !== "completed") return;
    try {
      const scenario = await createScenarioMutation.mutateAsync({
        network_id: result.network_id,
        name: "Recommended capacity upgrade",
        description: "Verified recommendation applied as an upgrade scenario.",
        modifications: [payload],
        initial_failures: result.initial_failures,
      });
      simMutation.mutate({
        network_id: result.network_id,
        initial_failures: result.initial_failures,
        scenario_id: scenario.id,
      });
    } catch (error) {
      console.error(error);
      alert(`Failed to apply recommendation: ${(error as Error).message}`);
    }
  };

  const handleResetTimeline = () => {
    if (result?.status === "completed") {
      setDismissedSimulationIds((prev) => {
        const next = new Set(prev);
        next.add(result.id);
        return next;
      });
    }
    reset();
  };

  const isRunning = simMutation.isPending || (polledResult && polledResult.status !== "completed" && polledResult.status !== "failed");

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Simulation Controls</h2>
        <select 
          style={{ background: "#1e293b", color: "white", padding: "4px 8px", borderRadius: 4, border: "1px solid #334155" }}
          value={mode}
          onChange={(e) => setMode(e.target.value as any)}
        >
          <option value="default">Baseline Simulation</option>
          <option value="add_redundancy">What-If: Add Redundancy</option>
        </select>
      </div>
      
      {mode === "default" && (
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 14, color: "#94a3b8", marginBottom: 8 }}>
            Selected Nodes for Initial Failure: {selectedNodeIds.size}
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleRunBaseline}
              disabled={selectedNodeIds.size === 0 || isRunning}
              style={{
                flex: 1,
                padding: "8px 16px",
                background: isRunning ? "#64748b" : (selectedNodeIds.size > 0 ? "#ef4444" : "#334155"),
                color: "white",
                border: "none",
                borderRadius: 4,
                cursor: (selectedNodeIds.size === 0 || isRunning) ? "not-allowed" : "pointer",
                fontWeight: "bold",
              }}
            >
              {isRunning ? "Running..." : "Simulate Baseline"}
            </button>
            <button
              onClick={clearSelection}
              disabled={selectedNodeIds.size === 0 || isRunning}
              style={{ padding: "8px 16px", background: "#334155", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {mode === "add_redundancy" && (
        <div style={{ marginBottom: 16, background: "#064e3b", padding: 12, borderRadius: 4, border: "1px solid #059669" }}>
          <p style={{ fontSize: 14, marginBottom: 8, color: "#a7f3d0" }}>
            1. Select exactly 2 nodes to add a redundant power line between.<br/>
            2. Make sure you also have initial failures selected (using Baseline mode).
          </p>
          <p style={{ fontSize: 13, marginBottom: 8 }}>Nodes selected: {redundancyNodes.length} / 2</p>
          <p style={{ fontSize: 13, marginBottom: 12 }}>Initial Failures ready: {selectedNodeIds.size}</p>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleSaveScenario}
              disabled={redundancyNodes.length !== 2 || selectedNodeIds.size === 0 || isRunning}
              style={{
                flex: 1,
                padding: "8px 16px",
                background: (redundancyNodes.length === 2 && selectedNodeIds.size > 0 && !isRunning) ? "#10b981" : "#334155",
                color: "white",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                fontWeight: "bold",
              }}
            >
              {isRunning ? "Running..." : "Save & Simulate"}
            </button>
            <button
              onClick={clearRedundancyNodes}
              style={{ padding: "8px 16px", background: "#334155", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {result && result.status === "completed" && (
        <div style={{ padding: 12, background: "#1e293b", borderRadius: 4, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: 14 }}>Simulation Results</h3>
          <p style={{ margin: "4px 0", fontSize: 13 }}>Waves: <span style={{ color: "#3b82f6" }}>{result.waves.length}</span></p>
          <p style={{ margin: "4px 0", fontSize: 13 }}>Failed Assets: <span style={{ color: "#ef4444" }}>{result.total_failed}</span></p>
          <p style={{ margin: "4px 0", fontSize: 13 }}>Pop Affected: <span style={{ color: "#f59e0b" }}>{result.population_affected_estimate.toLocaleString()}</span></p>
          {result.global_efficiency_before !== null && result.global_efficiency_after !== null && (
            <p style={{ margin: "4px 0", fontSize: 13 }}>Efficiency: <span style={{ color: "#22c55e" }}>{(result.global_efficiency_before * 100).toFixed(1)}%</span> → <span style={{ color: "#ef4444" }}>{(result.global_efficiency_after * 100).toFixed(1)}%</span></p>
          )}
        </div>
      )}

      {result && result.waves.length > 0 && (
        <CascadeTimeline
          waves={result.waves}
          currentWave={currentWave}
          isPlaying={isPlaying}
          onPlayPause={isPlaying ? pause : play}
          onReset={handleResetTimeline}
          onWaveChange={setWave}
        />
      )}
      <RecommendationPanel
        simulationId={result?.status === "completed" ? result.id : null}
        onApply={handleApplyRecommendation}
      />
    </div>
  );
};

export default ControlPanel;
