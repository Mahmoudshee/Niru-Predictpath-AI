import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Shield, Activity, Server, Clock } from "lucide-react";
import { useEffect, useState } from "react";

interface Alert {
  id: string;
  timestamp: string;
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  source: string;
  mitreTactic: string;
  mitreId: string;
  recommendation: string;
}

const mockAlerts: Alert[] = [
  {
    id: "1",
    timestamp: "12:34:56",
    severity: "critical",
    title: "Lateral Movement Detected via RDP",
    source: "DC-PRIMARY-01",
    mitreTactic: "Lateral Movement",
    mitreId: "T1021.001",
    recommendation: "Isolate host, disable RDP, revoke credentials",
  },
  {
    id: "2",
    timestamp: "12:32:18",
    severity: "high",
    title: "Credential Dumping Attempt",
    source: "WS-ADMIN-05",
    mitreTactic: "Credential Access",
    mitreId: "T1003",
    recommendation: "Force password reset, enable MFA",
  },
  {
    id: "3",
    timestamp: "12:28:42",
    severity: "medium",
    title: "Suspicious PowerShell Execution",
    source: "WS-DEV-12",
    mitreTactic: "Execution",
    mitreId: "T1059.001",
    recommendation: "Review script, check execution policy",
  },
  {
    id: "4",
    timestamp: "12:25:11",
    severity: "high",
    title: "Privilege Escalation via Token Manipulation",
    source: "DB-FINANCE-02",
    mitreTactic: "Privilege Escalation",
    mitreId: "T1134",
    recommendation: "Terminate session, audit token usage",
  },
];

const severityStyles = {
  critical: {
    bg: "bg-critical/15",
    border: "border-critical/40",
    badge: "bg-critical/20 text-critical",
    icon: "text-critical",
  },
  high: {
    bg: "bg-warning/10",
    border: "border-warning/30",
    badge: "bg-warning/20 text-warning",
    icon: "text-warning",
  },
  medium: {
    bg: "bg-primary/10",
    border: "border-primary/30",
    badge: "bg-primary/20 text-primary",
    icon: "text-primary",
  },
  low: {
    bg: "bg-muted",
    border: "border-border",
    badge: "bg-muted text-muted-foreground",
    icon: "text-muted-foreground",
  },
};

function AlertCard({ alert, index }: { alert: Alert; index: number }) {
  const styles = severityStyles[alert.severity];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 100 }}
      transition={{ delay: index * 0.05 }}
      className={`rounded-lg border p-4 ${styles.bg} ${styles.border}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className={`mt-0.5 ${styles.icon}`}>
            {alert.severity === "critical" ? (
              <AlertTriangle className="h-4 w-4 animate-pulse" />
            ) : (
              <Activity className="h-4 w-4" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm text-foreground line-clamp-1">
              {alert.title}
            </h4>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Server className="h-3 w-3" />
                {alert.source}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {alert.timestamp}
              </span>
            </div>
          </div>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${styles.badge}`}
        >
          {alert.severity}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
          <Shield className="h-3 w-3" />
          {alert.mitreTactic}
        </span>
        <span className="rounded bg-accent/20 px-2 py-0.5 text-[10px] font-mono text-accent">
          {alert.mitreId}
        </span>
      </div>

      <div className="mt-3 rounded bg-success/10 px-3 py-2">
        <p className="text-xs text-success">
          <span className="font-semibold">Action: </span>
          {alert.recommendation}
        </p>
      </div>
    </motion.div>
  );
}

export function AlertFeed() {
  const [alerts, setAlerts] = useState(mockAlerts);

  useEffect(() => {
    // Simulate new alerts coming in
    const interval = setInterval(() => {
      const newAlert: Alert = {
        id: Date.now().toString(),
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
        severity: ["critical", "high", "medium"][
          Math.floor(Math.random() * 3)
        ] as Alert["severity"],
        title: [
          "Anomalous Network Traffic Detected",
          "Failed Authentication Spike",
          "Suspicious Process Spawning",
          "Data Exfiltration Attempt",
        ][Math.floor(Math.random() * 4)],
        source: `HOST-${Math.floor(Math.random() * 100)
          .toString()
          .padStart(2, "0")}`,
        mitreTactic: ["Exfiltration", "Initial Access", "Persistence", "Defense Evasion"][
          Math.floor(Math.random() * 4)
        ],
        mitreId: `T${1000 + Math.floor(Math.random() * 600)}`,
        recommendation: "Investigate immediately and follow incident response procedures",
      };
      setAlerts((prev) => [newAlert, ...prev.slice(0, 3)]);
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-foreground">Predictive Alerts</h3>
          <p className="text-xs text-muted-foreground">
            AI-prioritized with MITRE ATT&CK mapping
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 animate-pulse rounded-full bg-success" />
          <span className="text-xs text-muted-foreground">Live</span>
        </div>
      </div>
      <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
        <AnimatePresence mode="popLayout">
          {alerts.map((alert, index) => (
            <AlertCard key={alert.id} alert={alert} index={index} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
