/**
 * Zustand store for simulation state.
 *
 * Manages the cascade animation: which nodes are failed, which wave
 * is currently displayed, and the full simulation result.
 */

import { create } from "zustand";
import type { CascadeWave, SimulationResult } from "../types";

interface SimulationState {
  /** The full simulation result object from the API */
  result: SimulationResult | null;
  /** Index of the currently-displayed wave (for animation) */
  currentWave: number;
  /** Set of node IDs that are failed up to the current wave */
  failedNodeIds: Set<string>;
  /** Whether the cascade animation is playing */
  isPlaying: boolean;
  /** Timer ID for the animation interval */
  animationTimer: ReturnType<typeof setTimeout> | null;

  // Actions
  setSimulationResult: (result: SimulationResult) => void;
  advanceWave: () => void;
  play: () => void;
  pause: () => void;
  reset: () => void;
  setWave: (index: number) => void;
}

export const useSimulationStore = create<SimulationState>((set, get) => ({
  result: null,
  currentWave: -1,
  failedNodeIds: new Set(),
  isPlaying: false,
  animationTimer: null,

  setSimulationResult: (result) => {
    const state = get();
    if (state.animationTimer) clearInterval(state.animationTimer);

    set({
      result,
      currentWave: -1,
      failedNodeIds: new Set(),
      isPlaying: false,
      animationTimer: null,
    });

    if (result.status === "completed" && result.waves.length > 0) {
      setTimeout(() => get().play(), 300);
    }
  },

  advanceWave: () => {
    const { result, currentWave, failedNodeIds, animationTimer } = get();
    if (!result || result.status !== "completed") return;
    
    const waves = result.waves;
    const nextWave = currentWave + 1;

    if (nextWave >= waves.length) {
      if (animationTimer) clearInterval(animationTimer);
      set({ isPlaying: false, animationTimer: null });
      return;
    }

    const newFailed = new Set(failedNodeIds);
    for (const id of waves[nextWave].failed_node_ids) {
      newFailed.add(id);
    }

    set({
      currentWave: nextWave,
      failedNodeIds: newFailed,
    });
  },

  play: () => {
    const { animationTimer, result, currentWave } = get();
    if (!result || result.status !== "completed") return;
    
    if (animationTimer) clearInterval(animationTimer);
    if (currentWave >= result.waves.length - 1) return;

    get().advanceWave();
    const timer = setInterval(() => {
      get().advanceWave();
    }, 800);

    set({ isPlaying: true, animationTimer: timer });
  },

  pause: () => {
    const { animationTimer } = get();
    if (animationTimer) clearInterval(animationTimer);
    set({ isPlaying: false, animationTimer: null });
  },

  reset: () => {
    const { animationTimer } = get();
    if (animationTimer) clearInterval(animationTimer);
    set({
      result: null,
      currentWave: -1,
      failedNodeIds: new Set(),
      isPlaying: false,
      animationTimer: null,
    });
  },

  setWave: (index) => {
    const { result } = get();
    if (!result || result.status !== "completed") return;
    
    const waves = result.waves;
    if (index < 0 || index >= waves.length) return;

    const newFailed = new Set<string>();
    for (let i = 0; i <= index; i++) {
      for (const id of waves[i].failed_node_ids) {
        newFailed.add(id);
      }
    }

    set({ currentWave: index, failedNodeIds: newFailed });
  },
}));
