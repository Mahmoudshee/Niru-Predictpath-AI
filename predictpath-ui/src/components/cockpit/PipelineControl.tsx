import { useState } from "react";
import { motion } from "framer-motion";
import {
  Database,
  GitBranch,
  Brain,
  Scale,
  Zap,
  GraduationCap,
  Play,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ToolConfig {
  id: number;
  name: string;
  description: string;
  icon: React.ElementType;
  command: string;
  inputPath: string;
  outputPath: string;
  isDestructive?: boolean;
  isAuto?: boolean;
  requiresApproval?: boolean;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: "pending" | "ready" | "error";
  serverPath?: string;
}

const tools: ToolConfig[] = [
  {
    id: 1,
    name: "Ingest Events",
    description: "Unified Event Intelligence Engine",
    icon: Database,
    command: ".\\.venv\\Scripts\\python.exe -m src.main ingest",
    inputPath: "[uploaded_log_files]",
    outputPath: "Tool1/ingestion_summary.json",
    isAuto: false,
  },
  {
    id: 2,
    name: "Build Sessions",
    description: "Temporal Attack Graph Engine",
    icon: GitBranch,
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool1\\data\\output\\**\\*.parquet",
    outputPath: "Tool2/path_report.json",
    isAuto: false,
  },
  {
    id: 3,
    name: "Forecast",
    description: "Predictive Adversary AI Engine",
    icon: Brain,
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool2\\path_report.json",
    outputPath: "Tool3/trajectory_forecast.json",
    isAuto: false,
  },
  {
    id: 4,
    name: "Decide",
    description: "Time-to-Compromise Intelligence",
    icon: Scale,
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool3\\trajectory_forecast.json",
    outputPath: "Tool4/response_plan.json",
    isAuto: false,
  },
  {
    id: 5,
    name: "Execute",
    description: "Decision & Risk Intelligence Engine",
    icon: Zap,
    command: ".\\.venv\\Scripts\\python.exe -m src.main",
    inputPath: "..\\Tool4\\response_plan.json",
    outputPath: "Tool5/execution_report.json",
    isDestructive: true,
    requiresApproval: true,
  },
  {
    id: 6,
    name: "Learn",
    description: "Explainable Security Experience",
    icon: GraduationCap,
    command: ".\\.venv\\Scripts\\python.exe -m src.main ingest",
    inputPath: "..\\Tool5\\execution_report.json",
    outputPath: "Tool6/status.json",
    isAuto: true,
  },
];

type ToolStatus = "idle" | "running" | "complete" | "error";

interface PipelineControlProps {
  onExecute: (tool: ToolConfig) => void;
  toolStatuses: Record<number, ToolStatus>;
  uploadedFiles?: UploadedFile[];
}

export const PipelineControl = ({ onExecute, toolStatuses, uploadedFiles = [] }: PipelineControlProps) => {
  const [confirmTool, setConfirmTool] = useState<ToolConfig | null>(null);

  const getStatusIcon = (status: ToolStatus) => {
    switch (status) {
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case "complete":
        return <CheckCircle2 className="h-4 w-4 text-success" />;
      case "error":
        return <AlertTriangle className="h-4 w-4 text-destructive" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: ToolStatus) => {
    switch (status) {
      case "running":
        return "border-primary/50 bg-primary/5";
      case "complete":
        return "border-success/50 bg-success/5";
      case "error":
        return "border-destructive/50 bg-destructive/5";
      default:
        return "border-border bg-card";
    }
  };

  const handleToolClick = (tool: ToolConfig) => {
    // Inject dynamic input path from uploaded files for Tool 1
    if (tool.id === 1 && uploadedFiles.length > 0) {
      const file = uploadedFiles[0];
      const path = file.serverPath || file.name;

      const fullCmd = `${tool.command} "${path}" --type lanl`;
      const execTool = {
        ...tool,
        command: fullCmd,
        inputPath: "" // Prevent Index.tsx from appending
      };
      onExecute(execTool);
      return;
    }

    if (tool.requiresApproval) {
      setConfirmTool(tool);
    } else {
      onExecute(tool);
    }
  };

  const handleConfirmExecution = () => {
    if (confirmTool) {
      onExecute(confirmTool);
      setConfirmTool(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Pipeline Control</h2>
        <p className="text-xs text-muted-foreground mt-1">
          Execute real CLI commands • Linear pipeline
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {tools.map((tool, index) => {
          const status = toolStatuses[tool.id] || "idle";
          const Icon = tool.icon;
          const isDisabled = status === "running" || (tool.id === 1 && uploadedFiles.length === 0);
          const needsFiles = tool.id === 1 && uploadedFiles.length === 0;

          let displayCommand = tool.command;
          if (tool.id === 1 && uploadedFiles.length > 0) {
            displayCommand = `${tool.command} "${uploadedFiles[0].serverPath || uploadedFiles[0].name}" --type lanl`;
          } else {
            displayCommand = `${tool.command} "${tool.inputPath}"`;
          }

          return (
            <motion.div
              key={tool.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <div
                className={`relative rounded-lg border p-3 transition-all ${getStatusColor(status)}`}
              >
                {/* Connector line */}
                {index < tools.length - 1 && (
                  <div className="absolute left-6 top-full h-2 w-px bg-border" />
                )}

                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${tool.isDestructive
                      ? "bg-destructive/20 text-destructive"
                      : "bg-primary/20 text-primary"
                      }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">
                        Tool {tool.id}
                      </span>
                      {tool.isDestructive && (
                        <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                          REAL / DESTRUCTIVE
                        </Badge>
                      )}
                      {tool.isAuto && (
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          AUTO
                        </Badge>
                      )}
                      {tool.requiresApproval && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-warning text-warning">
                          APPROVAL REQUIRED
                        </Badge>
                      )}
                    </div>
                    <h3 className="font-medium text-foreground">{tool.name}</h3>
                    <p className="text-xs text-muted-foreground whitespace-normal">
                      {tool.description}
                    </p>
                    <code className="mt-1.5 block text-[10px] font-mono text-muted-foreground/70 truncate">
                      {displayCommand}
                    </code>
                    {needsFiles && (
                      <p className="text-[10px] text-warning mt-1">↑ Upload log files above to enable</p>
                    )}
                  </div>

                  {/* Status & Action */}
                  <div className="flex items-center gap-2">
                    {getStatusIcon(status)}
                    <Button
                      size="sm"
                      variant={tool.isDestructive ? "destructive" : "default"}
                      disabled={isDisabled}
                      onClick={() => handleToolClick(tool)}
                      className="h-8 px-3"
                    >
                      {status === "running" ? (
                        "Running..."
                      ) : (
                        <>
                          <Play className="h-3 w-3 mr-1" />
                          Run
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Run All Pipeline */}
      <div className="p-4 border-t border-border">
        <Button className="w-full" size="lg">
          <ChevronRight className="h-4 w-4 mr-2" />
          Run Full Pipeline (Tool 1 → 6)
        </Button>
        <p className="text-[10px] text-muted-foreground text-center mt-2">
          Will pause at Tool 5 for approval
        </p>
      </div>

      {/* Confirmation Dialog for Destructive Actions */}
      <AlertDialog open={!!confirmTool} onOpenChange={() => setConfirmTool(null)}>
        <AlertDialogContent className="border-destructive/50">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Confirm Real System Execution
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>
                You are about to execute <strong>Tool {confirmTool?.id}: {confirmTool?.name}</strong>
              </p>
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-3">
                <p className="text-xs font-medium text-destructive mb-1">
                  ⚠️ This action will execute REAL system commands
                </p>
                <code className="text-[10px] font-mono text-muted-foreground block">
                  {confirmTool?.command} "{confirmTool?.inputPath}"
                </code>
              </div>
              <p className="text-sm">
                This may modify system state, network configurations, or security settings.
                This action cannot be undone.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmExecution}
              className="bg-destructive hover:bg-destructive/90"
            >
              Confirm Execution
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
