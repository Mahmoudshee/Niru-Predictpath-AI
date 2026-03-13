import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { TerminalLine } from "../components/cockpit/TerminalPanel";

export type ToolStatus = "idle" | "running" | "complete" | "error";

export interface UploadedFile {
  name: string;
  size: number;
  serverPath?: string;
  id: string;
  status: 'pending' | 'ready' | 'error';
}

export interface GovernanceState {
  trustThreshold: number | null;
  momentum: "rising" | "falling" | "stable" | null;
  streakCount: number | null;
  isConnected: boolean;
}

interface AppState {
  // Technical Tab State
  techTerminalLines: TerminalLine[];
  techToolStatuses: Record<number, ToolStatus>;
  techSystemStatus: "idle" | "running" | "error";
  techUploadedFiles: UploadedFile[];
  techToolResults: Record<number, any>; // Add toolResults here
  techSelectedToolId: number | null;
  techJsonData: any | null;
  techGovernanceState: GovernanceState;
  
  // Non-Technical Tab State
  nonTechTerminalLines: TerminalLine[];
  nonTechSystemStatus: "idle" | "running" | "error";
  nonTechActiveScan: string | null;
  
  // Actions - Technical
  setTechTerminalLines: (lines: TerminalLine[] | ((prev: TerminalLine[]) => TerminalLine[])) => void;
  addTechTerminalLine: (type: TerminalLine["type"], content: string) => void;
  setTechToolStatuses: (statuses: Record<number, ToolStatus> | ((prev: Record<number, ToolStatus>) => Record<number, ToolStatus>)) => void;
  setTechSystemStatus: (status: "idle" | "running" | "error") => void;
  setTechUploadedFiles: (files: UploadedFile[]) => void;
  setTechToolResults: (results: Record<number, any> | ((prev: Record<number, any>) => Record<number, any>)) => void;
  setTechSelectedToolId: (id: number | null) => void;
  setTechJsonData: (data: any | null) => void;
  setTechGovernanceState: (state: GovernanceState | ((prev: GovernanceState) => GovernanceState)) => void;

  // Actions - Non-Technical
  setNonTechTerminalLines: (lines: TerminalLine[] | ((prev: TerminalLine[]) => TerminalLine[])) => void;
  addNonTechTerminalLine: (type: TerminalLine["type"], content: string) => void;
  setNonTechSystemStatus: (status: "idle" | "running" | "error") => void;
  setNonTechActiveScan: (scan: string | null) => void;
  
  // Reset
  resetTechState: () => void;
  resetNonTechState: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Technical Tab State Initial
      techTerminalLines: [
        {
          id: "init-1",
          type: "info",
          content: "PredictPath AI Command Cockpit initialized",
          timestamp: new Date(),
        },
        {
          id: "init-2",
          type: "success",
          content: "Connected to Orchestration Backend.",
          timestamp: new Date(),
        },
      ],
      techToolStatuses: {},
      techSystemStatus: "idle",
      techUploadedFiles: [],
      techToolResults: {},
      techSelectedToolId: null,
      techJsonData: null,
      techGovernanceState: {
        trustThreshold: null,
        momentum: null,
        streakCount: null,
        isConnected: false,
      },
      
      // Non-Technical Tab State Initial
      nonTechTerminalLines: [
        {
          id: "init-1",
          type: "info",
          content: "PredictPath AI - Non-Technical Security Scanner",
          timestamp: new Date(),
        },
        {
          id: "init-2",
          type: "info",
          content: "Select a security scanner to begin guided analysis",
          timestamp: new Date(),
        },
      ],
      nonTechSystemStatus: "idle",
      nonTechActiveScan: null,
      
      // Technical Actions
      setTechTerminalLines: (updater) => set((state) => ({
        techTerminalLines: typeof updater === "function" ? updater(state.techTerminalLines) : updater,
      })),
      addTechTerminalLine: (type, content) => set((state) => ({
        techTerminalLines: [...state.techTerminalLines, {
          id: `line-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type,
          content,
          timestamp: new Date()
        }]
      })),
      setTechToolStatuses: (updater) => set((state) => ({
        techToolStatuses: typeof updater === "function" ? updater(state.techToolStatuses) : updater,
      })),
      setTechSystemStatus: (status) => set({ techSystemStatus: status }),
      setTechUploadedFiles: (files) => set({ techUploadedFiles: files }),
      setTechToolResults: (updater) => set((state) => ({
        techToolResults: typeof updater === "function" ? updater(state.techToolResults) : updater,
      })),
      setTechSelectedToolId: (id) => set({ techSelectedToolId: id }),
      setTechJsonData: (data) => set({ techJsonData: data }),
      setTechGovernanceState: (updater) => set((state) => ({
        techGovernanceState: typeof updater === "function" ? updater(state.techGovernanceState) : updater,
      })),

      // Non-Technical Actions
      setNonTechTerminalLines: (updater) => set((state) => ({
        nonTechTerminalLines: typeof updater === "function" ? updater(state.nonTechTerminalLines) : updater,
      })),
      addNonTechTerminalLine: (type, content) => set((state) => ({
        nonTechTerminalLines: [...state.nonTechTerminalLines, {
          id: `line-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type,
          content,
          timestamp: new Date()
        }]
      })),
      setNonTechSystemStatus: (status) => set({ nonTechSystemStatus: status }),
      setNonTechActiveScan: (scan) => set({ nonTechActiveScan: scan }),
      
      // Resets
      resetTechState: () => set({
        techTerminalLines: [{ id: "reset-1", type: "info", content: "Terminal Reset.", timestamp: new Date() }],
        techToolStatuses: {},
        techSystemStatus: "idle",
        techUploadedFiles: [],
        techToolResults: {},
        techSelectedToolId: null,
        techJsonData: null,
      }),
      resetNonTechState: () => set({
        nonTechTerminalLines: [{ id: "reset-1", type: "info", content: "Terminal Reset.", timestamp: new Date() }],
        nonTechSystemStatus: "idle",
        nonTechActiveScan: null
      })
    }),
    {
      name: "predictpath-storage", // name of the item in the storage (must be unique)
      storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
      partialize: (state) => ({
        // We only persist the data that is safe to deserialize.
        // Date objects in terminalLines will become strings via JSON stringify, but that's usually fine for display unless Date-specific methods are called.
        // If needed, we'll re-hydrate them.
        techTerminalLines: state.techTerminalLines,
        techToolStatuses: state.techToolStatuses,
        techUploadedFiles: state.techUploadedFiles,
        techToolResults: state.techToolResults,
        techSelectedToolId: state.techSelectedToolId,
        techJsonData: state.techJsonData,
        techGovernanceState: state.techGovernanceState,
        nonTechTerminalLines: state.nonTechTerminalLines,
        nonTechActiveScan: state.nonTechActiveScan,
        // Also persist status so UI shows it, but beware: if we load 'running', but backend dropped it, it's a desync.
        techSystemStatus: state.techSystemStatus,
        nonTechSystemStatus: state.nonTechSystemStatus
      }),
    }
  )
);
