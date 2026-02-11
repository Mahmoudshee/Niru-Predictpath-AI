import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

interface Node {
  id: string;
  label: string;
  type: "source" | "compromised" | "target" | "predicted";
  x: number;
  y: number;
}

interface Edge {
  from: string;
  to: string;
  type: "active" | "predicted";
}

const mockNodes: Node[] = [
  { id: "1", label: "WS-USER-01", type: "source", x: 50, y: 150 },
  { id: "2", label: "AD-SRV-01", type: "compromised", x: 180, y: 80 },
  { id: "3", label: "FILE-SRV-02", type: "compromised", x: 180, y: 220 },
  { id: "4", label: "DB-FIN-01", type: "predicted", x: 320, y: 150 },
  { id: "5", label: "DC-PRIMARY", type: "target", x: 450, y: 150 },
];

const mockEdges: Edge[] = [
  { from: "1", to: "2", type: "active" },
  { from: "1", to: "3", type: "active" },
  { from: "2", to: "4", type: "predicted" },
  { from: "3", to: "4", type: "predicted" },
  { from: "4", to: "5", type: "predicted" },
];

const nodeColors = {
  source: { fill: "hsl(186, 100%, 50%)", stroke: "hsl(186, 100%, 60%)" },
  compromised: { fill: "hsl(0, 85%, 55%)", stroke: "hsl(0, 85%, 65%)" },
  target: { fill: "hsl(38, 92%, 55%)", stroke: "hsl(38, 92%, 65%)" },
  predicted: { fill: "hsl(280, 100%, 65%)", stroke: "hsl(280, 100%, 75%)" },
};

export function AttackGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [animatedPaths, setAnimatedPaths] = useState<Set<string>>(new Set());

  useEffect(() => {
    const interval = setInterval(() => {
      setAnimatedPaths((prev) => {
        const newSet = new Set(prev);
        const randomEdge = mockEdges[Math.floor(Math.random() * mockEdges.length)];
        const key = `${randomEdge.from}-${randomEdge.to}`;
        if (newSet.has(key)) {
          newSet.delete(key);
        } else {
          newSet.add(key);
        }
        return newSet;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const getNodeById = (id: string) => mockNodes.find((n) => n.id === id);

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-4">
        <h3 className="font-semibold text-foreground">Temporal Attack Graph</h3>
        <p className="text-xs text-muted-foreground">
          Real-time attack path visualization
        </p>
      </div>
      <div className="relative aspect-[2/1] w-full overflow-hidden rounded-lg bg-secondary/30">
        <div className="absolute inset-0 cyber-grid opacity-50" />
        <svg
          ref={svgRef}
          viewBox="0 0 520 300"
          className="h-full w-full"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id="activeEdge" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="hsl(0, 85%, 55%)" />
              <stop offset="100%" stopColor="hsl(0, 85%, 65%)" />
            </linearGradient>
            <linearGradient id="predictedEdge" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="hsl(280, 100%, 55%)" />
              <stop offset="100%" stopColor="hsl(280, 100%, 75%)" />
            </linearGradient>
          </defs>

          {/* Edges */}
          {mockEdges.map((edge) => {
            const from = getNodeById(edge.from);
            const to = getNodeById(edge.to);
            if (!from || !to) return null;
            const key = `${edge.from}-${edge.to}`;
            const isAnimated = animatedPaths.has(key);

            return (
              <g key={key}>
                <motion.line
                  x1={from.x + 35}
                  y1={from.y}
                  x2={to.x - 35}
                  y2={to.y}
                  stroke={edge.type === "active" ? "url(#activeEdge)" : "url(#predictedEdge)"}
                  strokeWidth={isAnimated ? 3 : 2}
                  strokeDasharray={edge.type === "predicted" ? "8,4" : "none"}
                  opacity={isAnimated ? 1 : 0.6}
                  filter={isAnimated ? "url(#glow)" : "none"}
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.5, ease: "easeInOut" }}
                />
                {/* Arrow */}
                <polygon
                  points={`${to.x - 35},${to.y} ${to.x - 45},${to.y - 6} ${to.x - 45},${to.y + 6}`}
                  fill={edge.type === "active" ? "hsl(0, 85%, 55%)" : "hsl(280, 100%, 65%)"}
                  opacity={0.8}
                />
              </g>
            );
          })}

          {/* Nodes */}
          {mockNodes.map((node, index) => {
            const colors = nodeColors[node.type];
            return (
              <motion.g
                key={node.id}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: index * 0.15, type: "spring" }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={28}
                  fill={colors.fill}
                  opacity={0.15}
                  filter="url(#glow)"
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={20}
                  fill="hsl(222, 47%, 10%)"
                  stroke={colors.stroke}
                  strokeWidth={2}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={6}
                  fill={colors.fill}
                />
                <text
                  x={node.x}
                  y={node.y + 38}
                  textAnchor="middle"
                  className="fill-foreground text-[9px] font-mono"
                >
                  {node.label}
                </text>
              </motion.g>
            );
          })}
        </svg>

        {/* Legend */}
        <div className="absolute bottom-2 left-2 flex flex-wrap gap-3 rounded bg-background/80 px-2 py-1.5 text-[10px] backdrop-blur-sm">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" />
            <span className="text-muted-foreground">Source</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-critical" />
            <span className="text-muted-foreground">Compromised</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" />
            <span className="text-muted-foreground">Predicted</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-warning" />
            <span className="text-muted-foreground">Target</span>
          </div>
        </div>
      </div>
    </div>
  );
}
