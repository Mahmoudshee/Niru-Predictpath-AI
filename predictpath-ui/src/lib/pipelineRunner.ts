import { useAppStore } from "@/store/useAppStore";

const WS_BASE = `ws://${window.location.host}`;
const API_BASE = "";

export const tools = [
  {
    id: 1,
    name: "Ingest Events",
    description: "Unified Event Intelligence Engine",
    command: ".\\.venv\\Scripts\\python.exe run_tool1.py",
    inputPath: "[uploaded_log_files]",
    outputPath: "Tool1/ingestion_summary.json",
    isAuto: false,
  },
  {
    id: 2,
    name: "Build Sessions",
    description: "Temporal Attack Graph Engine",
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool1\\data\\output\\**\\*.parquet",
    outputPath: "Tool2/path_report.json",
    isAuto: false,
  },
  {
    id: 3,
    name: "Forecast",
    description: "Predictive Adversary AI Engine",
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool2\\path_report.json",
    outputPath: "Tool3/trajectory_forecast.json",
    isAuto: false,
  },
  {
    id: 4,
    name: "Decide",
    description: "Time-to-Compromise Intelligence",
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool3\\trajectory_forecast.json",
    outputPath: "Tool4/response_plan.json",
    isAuto: false,
  },
  {
    id: 5,
    name: "Execute",
    description: "Decision & Risk Intelligence Engine",
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool4\\response_plan.json",
    outputPath: "Tool5/execution_report.json",
    isScriptGen: true,
    requiresApproval: true,
  },
  {
    id: 6,
    name: "Learn",
    description: "Explainable Security Experience",
    command: ".\\.venv\\Scripts\\python.exe -m src.main ingest",
    inputPath: "..\\Tool5\\execution_report.json",
    outputPath: "Tool6/status.json",
    isAuto: true,
  },
];

export const getIngestType = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'xml') return 'universal';    
  if (ext === 'json' || ext === 'ndjson') return 'universal'; 
  if (ext === 'log') return 'universal';    
  if (ext === 'csv' || ext === 'gz' || ext === 'txt') return 'lanl'; 
  return 'universal'; 
};

export const fetchToolResult = async (path: string, toolId?: number) => {
  const store = useAppStore.getState();
  try {
    const res = await fetch(`${API_BASE}/api/file?path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error("File not found");
    const data = await res.json();
    try {
      const parsed = JSON.parse(data.content);
      store.setTechJsonData(parsed);

      const targetId = toolId || store.techSelectedToolId;
      if (targetId) {
        store.setTechToolResults((prev) => ({ ...prev, [targetId]: parsed }));
      }

      store.addTechTerminalLine("success", `Results loaded from ${path}`);

      // Auto update Governance state if we just loaded Tool 6 output
      if (path.includes("status.json")) {
        const statusData = parsed;
        if (statusData && !statusData.error) {
          store.setTechGovernanceState((prev) => ({
            ...prev,
            trustThreshold: statusData.containment_threshold ?? prev.trustThreshold,
            momentum: statusData.trend === 'relaxing' ? 'rising' : statusData.trend === 'tightening' ? 'falling' : 'stable',
            streakCount: statusData.success_streak ?? prev.streakCount,
            isConnected: true
          }));
        }
      }

    } catch (e) {
      store.setTechJsonData({ raw: data.content });
    }
  } catch (err) {
    store.addTechTerminalLine("warning", `Could not load result file: ${path}`);
  }
};

export const executeTool = (tool: any, isAborted?: () => boolean): Promise<void> => {
  const store = useAppStore.getState();
  
  return new Promise<void>((resolve, reject) => {
    if (isAborted && isAborted()) {
       reject(new Error("Aborted"));
       return;
    }
    
    let fullCommand = tool.command;
    if (tool.inputPath && !fullCommand.includes(tool.inputPath)) {
      if (tool.inputPath !== "") {
        fullCommand = `${fullCommand} "${tool.inputPath}"`;
      }
    }

    store.addTechTerminalLine("command", fullCommand);
    store.addTechTerminalLine("info", `Executing Tool ${tool.id}: ${tool.name}...`);

    store.setTechToolStatuses((prev) => ({ ...prev, [tool.id]: "running" }));
    store.setTechSystemStatus("running");
    store.setTechSelectedToolId(tool.id);
    store.setTechJsonData(null); 

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
      const exitMatch = msg.match(/\[Process exited with code (\d+)\]/);
      if (exitMatch) {
        exitCode = parseInt(exitMatch[1], 10);
      }

      let type: "info" | "success" | "error" | "warning" | "command" = "info";
      const upper = msg.toUpperCase();

      if (msg.includes("✅") || msg.includes("PASS") || msg.includes("COMPLETE")) {
        type = "success";
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

      store.addTechTerminalLine(type, msg.trim());
    };

    ws.onclose = async () => {
      const succeeded = exitCode === 0 || exitCode === null;

      if (succeeded) {
        store.setTechToolStatuses((prev) => ({ ...prev, [tool.id]: "complete" }));
        store.addTechTerminalLine("success", `✅ Tool ${tool.id} Execution Finished.`);
      } else {
        store.setTechToolStatuses((prev) => ({ ...prev, [tool.id]: "error" }));
        store.addTechTerminalLine("error", `✖ Tool ${tool.id} exited with code ${exitCode}.`);
      }
      store.setTechSystemStatus("idle");

      if (tool.outputPath && tool.outputPath.endsWith(".json") && succeeded) {
        await new Promise(r => setTimeout(r, 1500));
        await fetchToolResult(tool.outputPath, tool.id);
      }

      if (succeeded) {
        resolve();
      } else {
        reject(new Error(`Tool ${tool.id} failed`));
      }
    };

    ws.onerror = (err) => {
      store.addTechTerminalLine("error", "WebSocket Error: Failed to connect to backend.");
      store.setTechToolStatuses((prev) => ({ ...prev, [tool.id]: "error" }));
      store.setTechSystemStatus("error");
      reject(new Error("WebSocket Error"));
    };
  });
};

export const runFullPipeline = async (uploadedFile: any, isAborted?: () => boolean) => {
  const store = useAppStore.getState();
  
  if (!uploadedFile) {
     store.addTechTerminalLine("error", "Cannot run pipeline without an uploaded file.");
     return;
  }
  
  store.setTechUploadedFiles([uploadedFile]);
  store.addTechTerminalLine("info", `Pipeline initiated on auto-uploaded file: ${uploadedFile.name}`);

  // Need to clear tech statuses first
  store.setTechToolStatuses({});
  store.setTechToolResults({});

  for (const tool of tools) {
    if (isAborted && isAborted()) {
      break;
    }
    
    let execTool: any = { ...tool };
    if (tool.id === 1) {
      const serverPathStr = uploadedFile.serverPath || uploadedFile.name;
      // Tool 1 executes from inside "Tool1/". Adjust path relative to TOOLS_ROOT.
      let finalPath = serverPathStr;
      if (!finalPath.startsWith("..") && !finalPath.includes(":\\") && !finalPath.startsWith("/")) {
          finalPath = `..\\${finalPath}`;
      }
      
      const ingestType = getIngestType(uploadedFile.name);
      execTool.command = `${tool.command} "${finalPath}" --type ${ingestType}`;
      execTool.inputPath = "";
    }

    try {
      store.addNonTechTerminalLine("command", `[AUTOPILOT] Executing ${tool.name}...`);
      await executeTool(execTool, isAborted);
      // add a small pause between tools
      await new Promise(r => setTimeout(r, 1000));
    } catch (e) {
      const abortMsg = `Pipeline aborted at Tool ${tool.id}: ${e}`;
      store.addTechTerminalLine("error", abortMsg);
      store.addNonTechTerminalLine("error", `[AUTOPILOT] ${abortMsg}`);
      break; 
    }
    
    if (isAborted && isAborted()) {
      store.addNonTechTerminalLine("warning", `[AUTOPILOT] Pipeline execution stopped by Kill Switch.`);
      break;
    }
  }
  
  store.addTechTerminalLine("success", `Pipeline finished for file: ${uploadedFile.name}`);
  store.addNonTechTerminalLine("success", `[AUTOPILOT] Pipeline finished for file: ${uploadedFile.name}`);
};
