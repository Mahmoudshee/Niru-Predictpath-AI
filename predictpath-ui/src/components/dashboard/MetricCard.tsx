import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  variant?: "default" | "critical" | "success" | "warning";
}

const variantStyles = {
  default: "border-primary/30 bg-gradient-to-br from-primary/10 to-transparent",
  critical: "border-critical/30 bg-gradient-to-br from-critical/10 to-transparent",
  success: "border-success/30 bg-gradient-to-br from-success/10 to-transparent",
  warning: "border-warning/30 bg-gradient-to-br from-warning/10 to-transparent",
};

const iconStyles = {
  default: "text-primary",
  critical: "text-critical",
  success: "text-success",
  warning: "text-warning",
};

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  variant = "default",
}: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`relative overflow-hidden rounded-lg border p-5 ${variantStyles[variant]}`}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold font-mono tracking-tight text-foreground">
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
        <div className={`rounded-lg bg-secondary p-2.5 ${iconStyles[variant]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {trend && trendValue && (
        <div className="mt-3 flex items-center gap-1 text-xs">
          <span
            className={
              trend === "up"
                ? "text-success"
                : trend === "down"
                ? "text-critical"
                : "text-muted-foreground"
            }
          >
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
          </span>
          <span className="text-muted-foreground">vs last hour</span>
        </div>
      )}
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-gradient-to-br from-primary/5 to-transparent blur-2xl" />
    </motion.div>
  );
}
