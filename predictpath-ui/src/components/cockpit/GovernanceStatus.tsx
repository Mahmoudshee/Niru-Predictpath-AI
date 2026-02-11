import { motion } from "framer-motion";
import {
  Database,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Shield,
  Lock,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface GovernanceStatusProps {
  // These will be populated from real Tool6 output
  trustThreshold: number | null;
  momentum: "rising" | "falling" | "stable" | null;
  streakCount: number | null;
  isConnected: boolean;
}

export const GovernanceStatus = ({
  trustThreshold,
  momentum,
  streakCount,
  isConnected,
}: GovernanceStatusProps) => {
  const getMomentumIcon = () => {
    switch (momentum) {
      case "rising":
        return <TrendingUp className="h-4 w-4 text-success" />;
      case "falling":
        return <TrendingDown className="h-4 w-4 text-destructive" />;
      case "stable":
        return <Minus className="h-4 w-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const getMomentumLabel = () => {
    switch (momentum) {
      case "rising":
        return "Improving";
      case "falling":
        return "Declining";
      case "stable":
        return "Stable";
      default:
        return "Unknown";
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card/50 p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-foreground">
            Tool 6: Governance State
          </span>
        </div>
        <Badge
          variant={isConnected ? "outline" : "secondary"}
          className={`text-[10px] ${
            isConnected ? "border-success/50 text-success" : ""
          }`}
        >
          <Lock className="h-2.5 w-2.5 mr-1" />
          {isConnected ? "governance.db" : "Not Loaded"}
        </Badge>
      </div>

      {!isConnected ? (
        <div className="text-center py-6 text-muted-foreground">
          <Database className="h-10 w-10 mx-auto mb-3 opacity-20" />
          <p className="text-xs">Governance database not loaded</p>
          <p className="text-[10px] mt-1">Run Tool 6 to initialize or load existing state</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Trust Threshold */}
          <div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-muted-foreground">Trust Threshold</span>
              <span className="font-mono font-medium text-foreground">
                {trustThreshold !== null ? `${trustThreshold}%` : "--"}
              </span>
            </div>
            <Progress
              value={trustThreshold ?? 0}
              className="h-2"
            />
            <p className="text-[10px] text-muted-foreground mt-1">
              Read-only • Adjusted by learning engine
            </p>
          </div>

          {/* Momentum */}
          <div className="flex items-center justify-between py-2 border-t border-border">
            <span className="text-xs text-muted-foreground">Momentum</span>
            <div className="flex items-center gap-2">
              {getMomentumIcon()}
              <span className="text-xs font-medium">{getMomentumLabel()}</span>
            </div>
          </div>

          {/* Streak */}
          <div className="flex items-center justify-between py-2 border-t border-border">
            <span className="text-xs text-muted-foreground">Current Streak</span>
            <div className="flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-warning" />
              <span className="text-xs font-medium font-mono">
                {streakCount !== null ? streakCount : "--"}
              </span>
            </div>
          </div>

          {/* Protected Notice */}
          <div className="mt-4 rounded-md bg-primary/5 border border-primary/20 p-2">
            <div className="flex items-start gap-2">
              <Shield className="h-3.5 w-3.5 text-primary mt-0.5 shrink-0" />
              <p className="text-[10px] text-muted-foreground">
                Tool 6 maintains persistent state. Never auto-reset without explicit user consent.
                Use Reset Controls to manage governance state.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
