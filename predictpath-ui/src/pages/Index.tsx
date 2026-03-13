import { useState, useCallback, useEffect, useRef } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { motion } from "framer-motion";
import { CockpitHeader } from "@/components/cockpit/CockpitHeader";
import { PipelineControl } from "@/components/cockpit/PipelineControl";
import { TerminalPanel, TerminalLine } from "@/components/cockpit/TerminalPanel";
import { ResultsPanel } from "@/components/cockpit/ResultsPanel";
import { GovernanceStatus } from "@/components/cockpit/GovernanceStatus";
import { FileUploadPanel, UploadedFile } from "@/components/cockpit/FileUploadPanel";
import { ResetLevel } from "@/components/cockpit/ResetControls";
import { useAppStore } from "@/store/useAppStore";

type ToolStatus = "idle" | "running" | "complete" | "error";

const WS_BASE = `ws://${window.location.host}`;
const API_BASE = "";

const Index = () => {
  const {
    techToolStatuses: toolStatuses,
    setTechToolStatuses: setToolStatuses,
    techSystemStatus: systemStatus,
    setTechSystemStatus: setSystemStatus,
    techUploadedFiles: uploadedFiles,
    setTechUploadedFiles: setUploadedFiles,
    techTerminalLines: terminalLines,
    setTechTerminalLines: setTerminalLines,
    addTechTerminalLine: addTerminalLine,
    techToolResults: toolResults,
    setTechToolResults: setToolResults,
    techSelectedToolId: selectedToolId,
    setTechSelectedToolId: setSelectedToolId,
    techJsonData: jsonData,
    setTechJsonData: setJsonData,
    techGovernanceState: governanceState,
    setTechGovernanceState: setGovernanceState,
    resetTechState,
  } = useAppStore();

  // Responsive Layout Direction
  const [layoutDirection, setLayoutDirection] = useState<"horizontal" | "vertical">("horizontal");

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setLayoutDirection("vertical");
      } else {
        setLayoutDirection("horizontal");
      }
    };
    handleResize(); // Init
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Clear terminal
  const handleClearTerminal = useCallback(() => {
    setTerminalLines([
      {
        id: `clear-${Date.now()}`,
        type: "info",
        content: "Terminal cleared",
        timestamp: new Date(),
      },
    ]);
  }, []);

  // Fetch Results Helper
  const fetchToolResult = async (path: string, toolId?: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/file?path=${encodeURIComponent(path)}`);
      if (!res.ok) throw new Error("File not found");
      const data = await res.json();
      // The backend returns { content: string }
      // We need to parse the content string into JSON object
      try {
        const parsed = JSON.parse(data.content);
        setJsonData(parsed);

        const targetId = toolId || selectedToolId;
        if (targetId) {
          setToolResults(prev => ({ ...prev, [targetId]: parsed }));
        }

        addTerminalLine("success", `Results loaded from ${path}`);

        // Sync Governance State if applicable
        if (path.includes("status.json")) {
          const statusData = parsed;
          if (statusData && !statusData.error) {
            setGovernanceState({
              trustThreshold: statusData.containment_threshold,
              momentum: statusData.trend === 'relaxing' ? 'rising' : statusData.trend === 'tightening' ? 'falling' : 'stable',
              streakCount: statusData.success_streak,
              isConnected: true
            });
          }
        }

      } catch (e) {
        setJsonData({ raw: data.content }); // Fallback for non-JSON
      }
    } catch (err) {
      addTerminalLine("warning", `Could not load result file: ${path}`);
    }
  };

  // Setup Kill Switch Ref
  const isAbortedRef = useRef(false);

  const handleKillAll = useCallback(async () => {
    isAbortedRef.current = true;
    addTerminalLine("command", ">>> KILL SWITCH ACTIVATED <<<");
    addTerminalLine("warning", "Terminating all active processes...");
    try {
      const res = await fetch(`${API_BASE}/api/kill-all`, { method: "POST" });
      const data = await res.json();
      addTerminalLine("warning", data.message || "All processes terminated.");
    } catch (e) {
      addTerminalLine("error", "Failed to contact Kill Switch backend");
    }
    setSystemStatus("idle");
  }, [addTerminalLine]);


  // Handle tool execution
  const handleExecuteTool = useCallback(
    (tool: { id: number; name: string; command: string; inputPath: string; outputPath?: string }) => {
      return new Promise<void>((resolve, reject) => {
        let fullCommand = tool.command;
        if (tool.inputPath && !fullCommand.includes(tool.inputPath)) {
          if (tool.inputPath !== "") {
            fullCommand = `${fullCommand} "${tool.inputPath}"`;
          }
        }

        addTerminalLine("command", fullCommand);
        addTerminalLine("info", `Executing Tool ${tool.id}: ${tool.name}...`);

        setToolStatuses((prev) => ({ ...prev, [tool.id]: "running" }));
        setSystemStatus("running");
        setSelectedToolId(tool.id);
        setJsonData(null); // Clear previous results

        let exitCode: number | null = null;

        const ws = new WebSocket(`${WS_BASE}/ws/run`);

        ws.onopen = () => {
          ws.send(JSON.stringify({
            tool_dir: `Tool${tool.id}`,
            command: fullCommand
          }));
        };

        ws.onmessage = (event) => {
          const msg: string = event.data;

          // Parse exit code from backend sentinel line
          const exitMatch = msg.match(/\[Process exited with code (\d+)\]/);
          if (exitMatch) {
            exitCode = parseInt(exitMatch[1], 10);
          }

          // Classify line type — only flag REAL fatal failures
          let type: TerminalLine["type"] = "info";
          const upper = msg.toUpperCase();

          // Success indicators
          if (msg.includes("✅") || msg.includes("PASS") || msg.includes("COMPLETE")) {
            type = "success";
          // Fatal error indicators — NOT warnings/info logs
          } else if (
            upper.includes("TRACEBACK") ||
            upper.includes("EXCEPTION") ||
            upper.includes("FATAL") ||
            upper.includes("BACKEND ERROR") ||
            upper.startsWith("ERROR:") ||
            msg.includes("[Process exited with code 1]") ||
            msg.includes("[Process exited with code 2]")
          ) {
            type = "error";
          } else if (msg.includes("WARNING") || msg.includes("⚠")) {
            type = "warning";
          }

          addTerminalLine(type, msg.trim());
        };

        ws.onclose = async () => {
          const succeeded = exitCode === 0 || exitCode === null;

          if (succeeded) {
            setToolStatuses((prev) => ({ ...prev, [tool.id]: "complete" }));
            addTerminalLine("success", `✅ Tool ${tool.id} Execution Finished.`);
          } else {
            setToolStatuses((prev) => ({ ...prev, [tool.id]: "error" }));
            addTerminalLine("error", `✖ Tool ${tool.id} exited with code ${exitCode}.`);
          }
          setSystemStatus("idle");

          // Auto-fetch results if JSON — wait 1.5s so the file is fully written
          if (tool.outputPath && tool.outputPath.endsWith(".json") && succeeded) {
            await new Promise(r => setTimeout(r, 1500));
            await fetchToolResult(tool.outputPath, tool.id);
          }

          resolve();
        };

        ws.onerror = (err) => {
          addTerminalLine("error", "WebSocket Error: Failed to connect to backend.");
          setToolStatuses((prev) => ({ ...prev, [tool.id]: "error" }));
          setSystemStatus("error");
          reject(new Error("WebSocket Error"));
        };
      });
    },
    [addTerminalLine, fetchToolResult]
  );

  // Handle reset
  const handleReset = useCallback(
    async (level: ResetLevel) => {
      resetTechState();
      setTerminalLines([
        {
          id: `reset-${Date.now()}`,
          type: "command",
          content: `# Initiating ${level.toUpperCase()} reset...`,
          timestamp: new Date(),
        },
      ]);

      if (level === "soft" || level === "hard") {
        try {
          const res = await fetch(`${API_BASE}/api/reset`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: level })
          });
          const data = await res.json();
          if (res.ok) {
            addTerminalLine("success", `Physical Artifacts Deleted: ${data.deleted.join(", ")}`);

            // AUTO-INIT TOOL 6 ON HARD RESET
            if (level === "hard") {
              addTerminalLine("info", "Auto-initializing Governance DB (Tool 6 Fresh State)...");

              // Small delay to ensure deletion is processed by OS
              setTimeout(() => {
                handleExecuteTool({
                  id: 6,
                  name: "Initialize Governance",
                  command: ".\\.venv\\Scripts\\python.exe -m src.main init",
                  inputPath: "",
                  outputPath: ""
                });
              }, 1000);
            }

          } else {
            addTerminalLine("error", `Reset Failed: ${data.detail}`);
          }
        } catch (e) {
          addTerminalLine("error", "Backend Connection Failed for Reset.");
        }
      }

      switch (level) {
        case "soft":
          addTerminalLine("info", "UI State Cleared. Preserving Governance DB.");
          break;
        case "hard":
          addTerminalLine("warning", "Full Reset Complete. Governance Learning Cleared.");
          setGovernanceState({
            trustThreshold: null,
            momentum: null,
            streakCount: null,
            isConnected: true,
          });
          setUploadedFiles([]);
          break;
        case "replay":
          addTerminalLine("info", "Replay mode active.");
          break;
      }

      setToolStatuses({});
      setSelectedToolId(null);
      setJsonData(null);
    },
    [addTerminalLine, handleExecuteTool]
  );

  const handleSyncIntel = useCallback(() => {
    addTerminalLine("command", "# Initiating Manual Vulnerability Intelligence Sync...");
    addTerminalLine("info", "[VulnIntel] Connecting to synchronization engine...");

    setSystemStatus("running");

    const ws = new WebSocket(`${WS_BASE}/ws/sync-vuln`);

    ws.onopen = () => {
      ws.send(JSON.stringify({ force: true }));
    };

    ws.onmessage = (event) => {
      const msg = event.data;
      let type: TerminalLine["type"] = "info";
      if (msg.includes("Error") || msg.includes("Failed")) type = "error";
      if (msg.includes("Success") || msg.includes("Complete") || msg.includes("✅")) type = "success";

      addTerminalLine(type, msg.trim());
    };

    ws.onclose = () => {
      setSystemStatus("idle");
      addTerminalLine("success", "[VulnIntel] Sync session closed.");
    };

    ws.onerror = (err) => {
      addTerminalLine("error", "[VulnIntel] Connection failed.");
      setSystemStatus("error");
    };
  }, [addTerminalLine]);

  const handleFilesReady = useCallback((files: UploadedFile[]) => {
    setUploadedFiles(files);
    if (files.length > 0) {
      addTerminalLine("info", `${files.length} log file(s) staged for Tool 1 ingestion`);
    }
  }, [addTerminalLine]);

  const handleClearFiles = useCallback(() => {
    setUploadedFiles([]);
    addTerminalLine("info", "Uploaded files cleared");
  }, [addTerminalLine]);

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      <div className="fixed inset-0 cyber-grid opacity-20 pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />

      <CockpitHeader
        onReset={handleReset}
        onSyncIntel={handleSyncIntel}
        onKillAll={handleKillAll}
        systemStatus={systemStatus}
      />

      <div className="flex-1 flex overflow-hidden relative z-10">
        {layoutDirection === "vertical" ? (
          // MOBILE / TABLET LAYOUT (Stacked)
          <div className="flex-1 flex flex-col overflow-y-auto">
            {/* LEFT PANEL (Control) - TOP */}
            <div className="w-full shrink-0 border-b border-border bg-card/30 flex flex-col">
              <div className="shrink-0">
                <FileUploadPanel onFilesReady={handleFilesReady} onClear={handleClearFiles} />
              </div>
              <div className="h-[350px] overflow-y-auto custom-scrollbar">
                <PipelineControl
                  onExecute={handleExecuteTool}
                  onKillAll={handleKillAll}
                  isAborted={() => isAbortedRef.current}
                  resetKillSwitch={() => { isAbortedRef.current = false; }}
                  toolStatuses={toolStatuses}
                  uploadedFiles={uploadedFiles}
                  toolResults={toolResults}
                />
              </div>
            </div>

            {/* CENTER PANEL (Terminal + Governance) - MIDDLE */}
            <div className="w-full h-[600px] shrink-0 border-b border-border flex flex-col bg-background">
              <PanelGroup direction="vertical">
                <Panel defaultSize={70} minSize={30} className="p-2 pb-1">
                  <TerminalPanel lines={terminalLines} onClear={handleClearTerminal} />
                </Panel>

                <PanelResizeHandle className="h-1 bg-border/30 hover:bg-primary/50 transition-colors cursor-row-resize" />

                <Panel defaultSize={30} minSize={10} className="p-2 pt-1">
                  <GovernanceStatus
                    trustThreshold={governanceState.trustThreshold}
                    momentum={governanceState.momentum}
                    streakCount={governanceState.streakCount}
                    isConnected={governanceState.isConnected}
                  />
                </Panel>
              </PanelGroup>
            </div>

            {/* RIGHT PANEL (Results) - BOTTOM */}
            <div className="w-full min-h-[600px] shrink-0 bg-card/30">
              <ResultsPanel selectedToolId={selectedToolId} jsonData={jsonData} />
            </div>
          </div>
        ) : (
          // DESKTOP LAYOUT (Resizable Panes)
          <PanelGroup direction="horizontal" className="flex-1">

            {/* LEFT PANEL (Control) */}
            <Panel defaultSize={18} minSize={15} className="bg-card/30 backdrop-blur-sm flex flex-col border-r border-border">
              <div className="shrink-0">
                <FileUploadPanel onFilesReady={handleFilesReady} onClear={handleClearFiles} />
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                <PipelineControl
                  onExecute={handleExecuteTool}
                  onKillAll={handleKillAll}
                  isAborted={() => isAbortedRef.current}
                  resetKillSwitch={() => { isAbortedRef.current = false; }}
                  toolStatuses={toolStatuses}
                  uploadedFiles={uploadedFiles}
                  toolResults={toolResults}
                />
              </div>
            </Panel>

            <PanelResizeHandle className="w-1 bg-border/50 hover:bg-primary/50 transition-colors" />

            {/* CENTER PANEL (Terminal + Governance) */}
            <Panel defaultSize={26} minSize={20} className="border-r border-border min-w-0">
              <PanelGroup direction="vertical">
                <Panel defaultSize={75} minSize={40} className="flex flex-col p-4 pb-2">
                  <div className="flex-1 min-h-0">
                    <TerminalPanel lines={terminalLines} onClear={handleClearTerminal} />
                  </div>
                </Panel>

                <PanelResizeHandle className="h-1 bg-border/30 hover:bg-primary/50 transition-colors cursor-row-resize" />

                <Panel defaultSize={25} minSize={10} className="p-4 pt-2 shrink-0">
                  <GovernanceStatus
                    trustThreshold={governanceState.trustThreshold}
                    momentum={governanceState.momentum}
                    streakCount={governanceState.streakCount}
                    isConnected={governanceState.isConnected}
                  />
                </Panel>
              </PanelGroup>
            </Panel>

            <PanelResizeHandle className="w-1 bg-border/50 hover:bg-primary/50 transition-colors" />

            {/* RIGHT PANEL (Results) */}
            <Panel defaultSize={56} minSize={30} className="bg-card/30 backdrop-blur-sm min-w-0">
              <ResultsPanel selectedToolId={selectedToolId} jsonData={jsonData} />
            </Panel>

          </PanelGroup>
        )}
      </div>

      <footer className="h-8 border-t border-border bg-card/50 px-4 flex items-center justify-between text-[10px] text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>PredictPath AI v1.0</span>
          <span className="text-border">|</span>
          <span>Command Cockpit UI Shell</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Real-Time CLI Integration Active</span>
          <span className="text-border">|</span>
          <span>Backend: Port 8000</span>
        </div>
      </footer>
    </div>
  );
};

export default Index;
