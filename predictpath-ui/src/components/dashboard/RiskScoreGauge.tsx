import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

interface RiskScoreGaugeProps {
  score: number;
  trend: "up" | "down" | "stable";
  trendValue: string;
}

export function RiskScoreGauge({
  score,
  trend,
  trendValue,
}: RiskScoreGaugeProps) {
  const circumference = 2 * Math.PI * 70;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getScoreColor = (s: number) => {
    if (s >= 80) return { stroke: "hsl(0, 85%, 55%)", text: "text-critical" };
    if (s >= 60) return { stroke: "hsl(38, 92%, 55%)", text: "text-warning" };
    if (s >= 40) return { stroke: "hsl(186, 100%, 50%)", text: "text-primary" };
    return { stroke: "hsl(142, 76%, 45%)", text: "text-success" };
  };

  const colors = getScoreColor(score);

  const getRiskLevel = (s: number) => {
    if (s >= 80) return "CRITICAL";
    if (s >= 60) return "HIGH";
    if (s >= 40) return "MEDIUM";
    return "LOW";
  };

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-4">
        <h3 className="font-semibold text-foreground">
          Enterprise Risk Score
        </h3>
        <p className="text-xs text-muted-foreground">
          AI-calculated threat posture
        </p>
      </div>

      <div className="flex flex-col items-center">
        <div className="relative">
          <svg
            width="180"
            height="180"
            viewBox="0 0 180 180"
            className="transform -rotate-90"
          >
            {/* Background circle */}
            <circle
              cx="90"
              cy="90"
              r="70"
              fill="none"
              stroke="hsl(var(--secondary))"
              strokeWidth="12"
            />
            {/* Progress circle */}
            <motion.circle
              cx="90"
              cy="90"
              r="70"
              fill="none"
              stroke={colors.stroke}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.5, ease: "easeOut" }}
              style={{
                filter: `drop-shadow(0 0 8px ${colors.stroke})`,
              }}
            />
          </svg>

          {/* Center content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.5, type: "spring" }}
              className={`font-mono text-4xl font-bold ${colors.text}`}
            >
              {score}
            </motion.span>
            <span className="text-xs text-muted-foreground">/ 100</span>
            <span
              className={`mt-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                score >= 80
                  ? "bg-critical/20 text-critical"
                  : score >= 60
                  ? "bg-warning/20 text-warning"
                  : score >= 40
                  ? "bg-primary/20 text-primary"
                  : "bg-success/20 text-success"
              }`}
            >
              {getRiskLevel(score)}
            </span>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2">
          {trend === "up" ? (
            <TrendingUp className="h-4 w-4 text-critical" />
          ) : trend === "down" ? (
            <TrendingDown className="h-4 w-4 text-success" />
          ) : (
            <Activity className="h-4 w-4 text-muted-foreground" />
          )}
          <span
            className={`text-sm font-medium ${
              trend === "up"
                ? "text-critical"
                : trend === "down"
                ? "text-success"
                : "text-muted-foreground"
            }`}
          >
            {trendValue}
          </span>
          <span className="text-xs text-muted-foreground">vs last hour</span>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-secondary/50 p-3">
          <p className="text-[10px] text-muted-foreground">Assets at Risk</p>
          <p className="font-mono text-xl font-bold text-foreground">47</p>
        </div>
        <div className="rounded-lg bg-secondary/50 p-3">
          <p className="text-[10px] text-muted-foreground">Attack Paths</p>
          <p className="font-mono text-xl font-bold text-foreground">12</p>
        </div>
      </div>
    </div>
  );
}
