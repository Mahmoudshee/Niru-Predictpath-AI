import { useState } from "react";
import { motion } from "framer-motion";
import {
  RotateCcw,
  Trash2,
  History,
  AlertTriangle,
  Database,
  FileX,
  Shield,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { Badge } from "@/components/ui/badge";

export type ResetLevel = "soft" | "hard" | "replay" | "logs";

interface ResetConfig {
  level: ResetLevel;
  title: string;
  description: string;
  icon: React.ElementType;
  danger: boolean;
  actions: string[];
  preserves: string[];
}

const resetConfigs: Record<ResetLevel, ResetConfig> = {
  logs: {
    level: "logs",
    title: "Clear Scan Logs",
    description: "Remove all saved Nmap/OpenVAS logs from scripts/saved-logs",
    icon: Trash2,
    danger: false,
    actions: ["Clear scripts/saved-logs folder"],
    preserves: ["Tool 1-6 Artifacts", "Governance DB"],
  },
  soft: {
    level: "soft",
    title: "New Run (Preserve Learning)",
    description: "Clear intermediate outputs, keep governance state",
    icon: RotateCcw,
    danger: false,
    actions: [
      "Clear Tool1 output folder",
      "Delete Tool2 risk_assessment.json",
      "Delete Tool3 trajectory_forecast.json",
      "Delete Tool4 response_plan.json",
      "Delete Tool5 execution_report.json",
    ],
    preserves: ["Tool6 governance.db", "Learning state", "Trust thresholds"],
  },
  hard: {
    level: "hard",
    title: "Full Reset (Clear Learning)",
    description: "Delete all outputs and reset governance to initial state",
    icon: Trash2,
    danger: true,
    actions: [
      "Clear ALL intermediate files",
      "Delete Tool6 governance.db",
      "Re-initialize Tool6 fresh",
      "Reset all trust thresholds",
    ],
    preserves: [],
  },
  replay: {
    level: "replay",
    title: "Replay Governance History",
    description: "Re-apply historical execution reports to Tool6",
    icon: History,
    danger: false,
    actions: [
      "Load historical execution reports",
      "Re-apply sequentially to Tool6",
      "Observe threshold evolution",
    ],
    preserves: ["Current governance.db (backed up)"],
  },
};

interface ResetControlsProps {
  onReset: (level: ResetLevel) => void;
  mode?: "technical" | "non-technical";
}

export const ResetControls = ({ onReset, mode = "technical" }: ResetControlsProps) => {
  const [confirmReset, setConfirmReset] = useState<ResetLevel | null>(null);
  const config = confirmReset ? resetConfigs[confirmReset] : null;

  const handleResetClick = (level: ResetLevel) => {
    setConfirmReset(level);
  };

  const handleConfirmReset = () => {
    if (confirmReset) {
      onReset(confirmReset);
      setConfirmReset(null);
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
            Reset
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-72">
          <DropdownMenuLabel className="text-xs text-muted-foreground">
            {mode === "non-technical" ? "Log Management" : "Reset Levels"}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {mode === "non-technical" ? (
            <DropdownMenuItem
              className="flex flex-col items-start p-3 cursor-pointer"
              onClick={() => handleResetClick("logs")}
            >
              <div className="flex items-center gap-2">
                <Trash2 className="h-4 w-4 text-primary" />
                <span className="font-medium">{resetConfigs.logs.title}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 ml-6">
                {resetConfigs.logs.description}
              </p>
            </DropdownMenuItem>
          ) : (
            <>
              {/* Soft Reset */}
              <DropdownMenuItem
                className="flex flex-col items-start p-3 cursor-pointer"
                onClick={() => handleResetClick("soft")}
              >
                <div className="flex items-center gap-2">
                  <RotateCcw className="h-4 w-4 text-primary" />
                  <span className="font-medium">{resetConfigs.soft.title}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 ml-6">
                  {resetConfigs.soft.description}
                </p>
              </DropdownMenuItem>

              {/* Hard Reset */}
              <DropdownMenuItem
                className="flex flex-col items-start p-3 cursor-pointer"
                onClick={() => handleResetClick("hard")}
              >
                <div className="flex items-center gap-2">
                  <Trash2 className="h-4 w-4 text-destructive" />
                  <span className="font-medium text-destructive">
                    {resetConfigs.hard.title}
                  </span>
                  <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                    DANGER
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 ml-6">
                  {resetConfigs.hard.description}
                </p>
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              {/* Replay Mode */}
              <DropdownMenuItem
                className="flex flex-col items-start p-3 cursor-pointer"
                onClick={() => handleResetClick("replay")}
              >
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-accent" />
                  <span className="font-medium">{resetConfigs.replay.title}</span>
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                    ADVANCED
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 ml-6">
                  {resetConfigs.replay.description}
                </p>
              </DropdownMenuItem>
            </>
          )}

        </DropdownMenuContent>
      </DropdownMenu>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!confirmReset} onOpenChange={() => setConfirmReset(null)}>
        <AlertDialogContent
          className={config?.danger ? "border-destructive/50" : "border-border"}
        >
          <AlertDialogHeader>
            <AlertDialogTitle
              className={`flex items-center gap-2 ${config?.danger ? "text-destructive" : ""
                }`}
            >
              {config?.icon && <config.icon className="h-5 w-5" />}
              {config?.title}
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p>{config?.description}</p>

              {/* Actions */}
              <div className="rounded-lg bg-muted/50 border border-border p-3">
                <p className="text-xs font-medium text-foreground mb-2 flex items-center gap-1.5">
                  <FileX className="h-3.5 w-3.5" />
                  This will:
                </p>
                <ul className="text-xs space-y-1">
                  {config?.actions.map((action, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Preserves */}
              {config?.preserves && config.preserves.length > 0 && (
                <div className="rounded-lg bg-success/10 border border-success/30 p-3">
                  <p className="text-xs font-medium text-success mb-2 flex items-center gap-1.5">
                    <Shield className="h-3.5 w-3.5" />
                    Preserved:
                  </p>
                  <ul className="text-xs space-y-1">
                    {config.preserves.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-success/80">
                        <span>•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {config?.danger && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-3">
                  <p className="text-xs font-medium text-destructive flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    This action will delete Tool6 learning state. This cannot be undone.
                  </p>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmReset}
              className={
                config?.danger ? "bg-destructive hover:bg-destructive/90" : ""
              }
            >
              Confirm {config?.level === "soft" ? "Reset" : config?.level === "hard" ? "Full Reset" : config?.level === "logs" ? "Clear Logs" : "Replay"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
