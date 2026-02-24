import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Database,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Shield,
  Lock,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Activity,
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

interface LiveGovernanceData {
  version_id?: string;
  containment_threshold?: number;
  disruptive_threshold?: number;
  trust_momentum?: number;
  success_streak?: number;
  failure_streak?: number;
  trend?: string;
  trend_label?: string;
  ledger_integrity?: boolean;
  ledger_entry_count?: number;
  drift_alerts?: string[];
  error?: string;
}

export const GovernanceStatus = ({
  trustThreshold,
  momentum,
  streakCount,
  isConnected,
}: GovernanceStatusProps) => {
  const [liveData, setLiveData] = useState<LiveGovernanceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastFetched, setLastFetched] = useState<Date | null>(null);

  const fetchLive = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/tool6/status");
      if (res.ok) {
        const data = await res.json();
        if (!data.error) {
          setLiveData(data);
          setLastFetched(new Date());
        }
      }
    } catch {
      // keep existing data
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on mount and every 30 seconds
  useEffect(() => {
    fetchLive();
    const interval = setInterval(fetchLive, 30000);
    return () => clearInterval(interval);
  }, []);

  // Use live data if available, otherwise fall back to props
  const displayThreshold =
    liveData?.containment_threshold != null
      ? Math.round(liveData.containment_threshold * 100)
      : trustThreshold;

  const displayMomentum =
    liveData?.trust_momentum != null
      ? liveData.trust_momentum > 0.001
        ? "rising"
        : liveData.trust_momentum < -0.001
          ? "falling"
          : "stable"
      : momentum;

  const displayStreak =
    liveData?.success_streak != null ? liveData.success_streak : streakCount;

  const hasLiveData = liveData != null && !liveData.error;
  const connected = hasLiveData || isConnected;

  const getMomentumIcon = () => {
    switch (displayMomentum) {
      case "rising":
        return <TrendingUp className="h-4 w-4 text-green-400" />;
      case "falling":
        return <TrendingDown className="h-4 w-4 text-red-400" />;
      case "stable":
        return <Minus className="h-4 w-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const getMomentumLabel = () => {
    if (liveData?.trend_label) return liveData.trend_label;
    switch (displayMomentum) {
      case "rising":
        return "Relaxing (Adapting)";
      case "falling":
        return "Tightening (Hardening)";
      case "stable":
        return "Stable";
      default:
        return "Unknown";
    }
  };

  const momentumColor =
    displayMomentum === "rising"
      ? "text-green-400"
      : displayMomentum === "falling"
        ? "text-red-400"
        : "text-muted-foreground";

  const driftAlerts = liveData?.drift_alerts ?? [];

  return (
    <div className="rounded-lg border border-border bg-card/40 p-2 space-y-2">
      {/* Dense Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-1.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <Database className="h-3.5 w-3.5 text-primary shrink-0" />
          <span className="text-[11px] font-bold text-foreground truncate">
            Governance State
          </span>
          {liveData?.version_id && (
            <span className="text-[9px] font-mono text-primary/60 ml-1 truncate max-w-[60px] hidden sm:inline">
              {liveData.version_id}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge
            variant={connected ? "outline" : "secondary"}
            className={`text-[9px] h-4 py-0 px-1 border-0 bg-white/5 ${connected ? "text-green-400" : ""}`}
          >
            {connected ? "governance.db" : "No DB"}
          </Badge>
          <button
            onClick={fetchLive}
            className="h-5 w-5 rounded flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <RefreshCw className={`h-2.5 w-2.5 text-muted-foreground ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {!connected ? (
        <div className="text-center py-2 text-[10px] text-muted-foreground opacity-50">
          Governance DB offline
        </div>
      ) : (
        <div className="space-y-2">
          {/* Drift Alerts - Restored wrapping for Auditing */}
          <AnimatePresence>
            {driftAlerts.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-1"
              >
                {driftAlerts.map((alert, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-1.5 p-1.5 rounded bg-yellow-500/10 border border-yellow-500/20 text-[9px] text-yellow-300 leading-tight"
                  >
                    <AlertTriangle className="h-2.5 w-2.5 shrink-0 mt-0.5" />
                    <span>{alert}</span>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Progress Section */}
          <div className="grid grid-cols-2 gap-3 pb-1">
            <div className="space-y-1">
              <div className="flex justify-between text-[10px]">
                <span className="text-muted-foreground">Containment</span>
                <span className="font-mono text-foreground font-bold">{displayThreshold}%</span>
              </div>
              <Progress value={displayThreshold ?? 0} className="h-1" />
            </div>
            {liveData?.disruptive_threshold != null && (
              <div className="space-y-1">
                <div className="flex justify-between text-[10px]">
                  <span className="text-muted-foreground">Disruptive</span>
                  <span className="font-mono text-red-400 font-bold">{Math.round(liveData.disruptive_threshold * 100)}%</span>
                </div>
                <Progress value={liveData.disruptive_threshold * 100} className="h-1 bg-red-950/20" />
              </div>
            )}
          </div>

          {/* Audit Metrics Row - RESTORED FOR AUDITING */}
          <div className="grid grid-cols-2 gap-1.5">
            <div className="flex items-center justify-between text-[9px] bg-white/5 px-2 py-1 rounded border border-white/5">
              <span className="text-muted-foreground flex items-center gap-1">
                <Activity className="h-2.5 w-2.5" /> Trace
              </span>
              <div className="flex items-center gap-2">
                <span className="text-green-400 font-bold" title="Successes">{displayStreak ?? 0}s</span>
                <span className="text-red-400 font-bold" title="Failures">{liveData?.failure_streak ?? 0}f</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-[9px] bg-white/5 px-2 py-1 rounded border border-white/5">
              <span className="text-muted-foreground">Ledger</span>
              <div className="flex items-center gap-1">
                {liveData?.ledger_integrity ? (
                  <span className="text-green-400 font-bold flex items-center gap-0.5"><CheckCircle2 className="h-2.5 w-2.5" />OK</span>
                ) : (
                  <span className="text-red-400 font-bold flex items-center gap-0.5"><AlertTriangle className="h-2.5 w-2.5" />FAIL</span>
                )}
                <span className="opacity-40 ml-0.5">({liveData?.ledger_entry_count ?? 0})</span>
              </div>
            </div>
          </div>

          {/* Momentum & Sync Row */}
          <div className="flex items-center justify-between text-[10px] pt-1">
            <div className="flex items-center gap-1.5 min-w-0">
              {getMomentumIcon()}
              <span className={`font-medium truncate ${momentumColor}`}>{getMomentumLabel()}</span>
            </div>
            {lastFetched && (
              <span className="text-[8px] text-muted-foreground/40 font-mono">
                {lastFetched.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
