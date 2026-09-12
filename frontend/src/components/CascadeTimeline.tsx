import React from "react";
import type { CascadeWave } from "../types";

interface CascadeTimelineProps {
  waves: CascadeWave[];
  currentWave: number;
  isPlaying: boolean;
  onPlayPause: () => void;
  onReset: () => void;
  onWaveChange: (index: number) => void;
}

export default function CascadeTimeline({
  waves,
  currentWave,
  isPlaying,
  onPlayPause,
  onReset,
  onWaveChange,
}: CascadeTimelineProps) {
  if (waves.length === 0) return null;

  const selectedWave = waves[Math.max(0, Math.min(currentWave, waves.length - 1))];
  const minuteLabel =
    selectedWave.simulated_minute === undefined
      ? ""
      : ` — ${selectedWave.simulated_minute} min`;
  const populationLabel =
    selectedWave.population_affected_estimate === undefined
      ? ""
      : ` — ${selectedWave.population_affected_estimate.toLocaleString()} affected`;

  return (
    <div style={{ marginTop: 12, padding: 12, background: "#0f172a", borderRadius: 4 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 14 }}>
          Wave {selectedWave.wave} / {waves.length - 1}
          {minuteLabel}
          {populationLabel}
        </span>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={onPlayPause} style={buttonStyle}>
            {isPlaying ? "Pause" : "Play"}
          </button>
          <button onClick={onReset} style={buttonStyle}>Reset</button>
        </div>
      </div>
      <input
        aria-label="Cascade timeline"
        type="range"
        min={0}
        max={waves.length - 1}
        value={Math.max(0, currentWave)}
        onChange={(event) => onWaveChange(Number(event.target.value))}
        style={{ width: "100%", marginTop: 10 }}
      />
    </div>
  );
}

const buttonStyle: React.CSSProperties = {
  padding: "5px 9px",
  background: "#334155",
  color: "white",
  border: "none",
  borderRadius: 4,
  cursor: "pointer",
};
