import React from "react";
import { useCentrality } from "../api/hooks";
import { useUIStore } from "../stores/uiStore";

const CriticalityPanel: React.FC = () => {
  const networkId = useUIStore((s) => s.networkId);
  const { data: scores, isLoading } = useCentrality(networkId);
  const toggleNodeSelection = useUIStore((s) => s.toggleNodeSelection);
  const selectedNodeIds = useUIStore((s) => s.selectedNodeIds);
  const hoverNode = useUIStore((s) => s.setHoveredNode);

  if (isLoading) {
    return <div style={{ padding: 16 }}>Loading criticality...</div>;
  }

  if (!scores) return null;

  // Take top 10
  const top10 = scores.slice(0, 10);
  const maxScore = top10.length > 0 ? top10[0].score : 1;

  return (
    <div style={{ padding: 16, borderTop: "1px solid #334155" }}>
      <h3 style={{ margin: "0 0 12px 0", fontSize: 16, fontWeight: 600 }}>Top Critical Nodes (PageRank)</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {top10.map((s, i) => {
          const isSelected = selectedNodeIds.has(s.node_id);
          const percent = (s.score / maxScore) * 100;
          return (
            <div 
              key={s.node_id}
              onClick={() => toggleNodeSelection(s.node_id)}
              onMouseEnter={() => hoverNode(s.node_id)}
              onMouseLeave={() => hoverNode(null)}
              style={{
                background: isSelected ? "#3b82f633" : "#1e293b",
                border: isSelected ? "1px solid #3b82f6" : "1px solid transparent",
                padding: "6px 8px",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: 12,
                position: "relative",
                overflow: "hidden"
              }}
            >
              {/* Progress bar background */}
              <div style={{ 
                position: "absolute", 
                left: 0, top: 0, bottom: 0, 
                width: `${percent}%`, 
                background: "#f59e0b", 
                opacity: 0.2,
                zIndex: 0
              }} />
              
              <div style={{ display: "flex", justifyContent: "space-between", position: "relative", zIndex: 1 }}>
                <span>#{i + 1} {s.node_id.split('-')[0]}</span>
                <span style={{ color: "#f59e0b", fontWeight: "bold" }}>{s.score.toFixed(2)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CriticalityPanel;
