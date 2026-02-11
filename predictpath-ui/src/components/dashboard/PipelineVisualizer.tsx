import { motion } from "framer-motion";
import {
  Database,
  GitBranch,
  Brain,
  Timer,
  BarChart3,
  Eye,
  ArrowRight,
} from "lucide-react";
import { useState } from "react";

interface PipelineStep {
  id: number;
  title: string;
  subtitle: string;
  icon: typeof Database;
  status: "active" | "processing" | "idle";
  metrics: { label: string; value: string }[];
}

const pipelineSteps: PipelineStep[] = [
  {
    id: 1,
    title: "Unified Event Intelligence",
    subtitle: "Ingest • Normalize • Enrich",
    icon: Database,
    status: "active",
    metrics: [
      { label: "Events/sec", value: "12.4K" },
      { label: "Sources", value: "47" },
    ],
  },
  {
    id: 2,
    title: "Temporal Attack Graph",
    subtitle: "Build • Discover • Update",
    icon: GitBranch,
    status: "active",
    metrics: [
      { label: "Nodes", value: "1,247" },
      { label: "Paths", value: "89" },
    ],
  },
  {
    id: 3,
    title: "Predictive Adversary AI",
    subtitle: "Learn • Predict • Adapt",
    icon: Brain,
    status: "processing",
    metrics: [
      { label: "Accuracy", value: "94.2%" },
      { label: "Predictions", value: "156" },
    ],
  },
  {
    id: 4,
    title: "Time-to-Compromise",
    subtitle: "Estimate • Update • Alert",
    icon: Timer,
    status: "active",
    metrics: [
      { label: "Avg TTC", value: "2.3h" },
      { label: "Critical", value: "3" },
    ],
  },
  {
    id: 5,
    title: "Risk Decision Engine",
    subtitle: "Prioritize • Score • Rank",
    icon: BarChart3,
    status: "active",
    metrics: [
      { label: "High Risk", value: "12" },
      { label: "Mitigated", value: "847" },
    ],
  },
  {
    id: 6,
    title: "Explainable Experience",
    subtitle: "Visualize • Explain • Act",
    icon: Eye,
    status: "active",
    metrics: [
      { label: "Narratives", value: "23" },
      { label: "Actions", value: "67" },
    ],
  },
];

const statusColors = {
  active: "border-success/50 bg-success/10",
  processing: "border-accent/50 bg-accent/10 animate-pulse",
  idle: "border-border bg-muted/30",
};

const iconColors = {
  active: "text-success",
  processing: "text-accent",
  idle: "text-muted-foreground",
};

export function PipelineVisualizer() {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-6">
        <h3 className="font-semibold text-foreground">
          6-Tool Intelligence Pipeline
        </h3>
        <p className="text-xs text-muted-foreground">
          Real-time processing status
        </p>
      </div>

      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-[50%] top-0 h-full w-px bg-gradient-to-b from-primary/50 via-accent/50 to-success/50 hidden lg:block" />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {pipelineSteps.map((step, index) => {
            const Icon = step.icon;
            const isHovered = hoveredStep === step.id;

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onMouseEnter={() => setHoveredStep(step.id)}
                onMouseLeave={() => setHoveredStep(null)}
                className={`relative rounded-lg border p-4 transition-all duration-300 cursor-pointer ${
                  statusColors[step.status]
                } ${isHovered ? "scale-[1.02] shadow-lg" : ""}`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`rounded-lg bg-secondary p-2 ${iconColors[step.status]}`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted-foreground">
                        0{step.id}
                      </span>
                      {step.status === "processing" && (
                        <span className="flex items-center gap-1 rounded-full bg-accent/20 px-1.5 py-0.5 text-[9px] font-medium text-accent">
                          <span className="h-1 w-1 animate-pulse rounded-full bg-accent" />
                          Processing
                        </span>
                      )}
                    </div>
                    <h4 className="mt-1 font-medium text-sm text-foreground line-clamp-1">
                      {step.title}
                    </h4>
                    <p className="text-[10px] text-muted-foreground">
                      {step.subtitle}
                    </p>
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-2">
                  {step.metrics.map((metric) => (
                    <div
                      key={metric.label}
                      className="rounded bg-background/50 px-2 py-1.5"
                    >
                      <p className="text-[9px] text-muted-foreground">
                        {metric.label}
                      </p>
                      <p className="font-mono text-sm font-semibold text-foreground">
                        {metric.value}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Arrow for flow indication */}
                {index < pipelineSteps.length - 1 && (
                  <div className="absolute -right-2 top-1/2 -translate-y-1/2 hidden sm:block lg:hidden">
                    <ArrowRight className="h-4 w-4 text-primary/50" />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-success" />
          <span>Active</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
          <span>Processing</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-muted-foreground" />
          <span>Idle</span>
        </div>
      </div>
    </div>
  );
}
