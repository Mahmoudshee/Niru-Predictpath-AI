import { motion } from "framer-motion";
import { Clock, AlertTriangle, Shield } from "lucide-react";
import { useEffect, useState } from "react";

interface TTCAsset {
  id: string;
  hostname: string;
  ttcMinutes: number;
  riskScore: number;
  attackVector: string;
  status: "critical" | "high" | "medium";
}

const mockAssets: TTCAsset[] = [
  {
    id: "1",
    hostname: "DC-PRIMARY-01",
    ttcMinutes: 47,
    riskScore: 93,
    attackVector: "Lateral Movement via RDP",
    status: "critical",
  },
  {
    id: "2",
    hostname: "DB-FINANCE-02",
    ttcMinutes: 124,
    riskScore: 78,
    attackVector: "Credential Harvesting",
    status: "high",
  },
  {
    id: "3",
    hostname: "WEB-PROD-03",
    ttcMinutes: 312,
    riskScore: 54,
    attackVector: "SQL Injection Chain",
    status: "medium",
  },
];

const statusStyles = {
  critical: {
    bg: "bg-critical/10",
    border: "border-critical/40",
    text: "text-critical",
    glow: "shadow-[0_0_15px_hsl(var(--critical)/0.3)]",
  },
  high: {
    bg: "bg-warning/10",
    border: "border-warning/40",
    text: "text-warning",
    glow: "",
  },
  medium: {
    bg: "bg-primary/10",
    border: "border-primary/40",
    text: "text-primary",
    glow: "",
  },
};

function formatTTC(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

function TTCAssetCard({ asset, index }: { asset: TTCAsset; index: number }) {
  const [ttc, setTtc] = useState(asset.ttcMinutes);
  const styles = statusStyles[asset.status];

  useEffect(() => {
    const interval = setInterval(() => {
      setTtc((prev) => Math.max(0, prev - 1));
    }, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`relative rounded-lg border p-4 ${styles.bg} ${styles.border} ${styles.glow}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            {asset.status === "critical" && (
              <AlertTriangle className="h-4 w-4 text-critical animate-pulse" />
            )}
            <h4 className="font-mono text-sm font-semibold text-foreground">
              {asset.hostname}
            </h4>
          </div>
          <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
            {asset.attackVector}
          </p>
        </div>
        <div className={`text-right ${styles.text}`}>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span className="font-mono text-lg font-bold">{formatTTC(ttc)}</span>
          </div>
          <p className="text-xs opacity-70">TTC</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Risk Score</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-20 rounded-full bg-secondary overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${asset.riskScore}%` }}
              transition={{ duration: 1, delay: index * 0.1 }}
              className={`h-full rounded-full ${
                asset.riskScore > 80
                  ? "bg-critical"
                  : asset.riskScore > 60
                  ? "bg-warning"
                  : "bg-primary"
              }`}
            />
          </div>
          <span className={`font-mono text-sm font-semibold ${styles.text}`}>
            {asset.riskScore}%
          </span>
        </div>
      </div>
    </motion.div>
  );
}

export function TTCCountdown() {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-foreground">Time-to-Compromise</h3>
          <p className="text-xs text-muted-foreground">
            Live breach countdown per asset
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-critical/20 px-2.5 py-1">
          <span className="h-2 w-2 animate-pulse rounded-full bg-critical" />
          <span className="text-xs font-medium text-critical">
            {mockAssets.filter((a) => a.status === "critical").length} Critical
          </span>
        </div>
      </div>
      <div className="space-y-3">
        {mockAssets.map((asset, index) => (
          <TTCAssetCard key={asset.id} asset={asset} index={index} />
        ))}
      </div>
    </div>
  );
}
