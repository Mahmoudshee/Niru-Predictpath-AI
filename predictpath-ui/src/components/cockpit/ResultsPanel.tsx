import { useState } from "react";
import { motion } from "framer-motion";
import {
  FileJson,
  Table as TableIcon,
  BarChart3,
  Activity,
  Shield,
  Zap,
  Lock,
  Unlock,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Database
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface ResultFile {
  toolId: number;
  filename: string;
  path: string;
  status: "pending" | "available" | "error";
}

const resultFiles: ResultFile[] = [
  { toolId: 1, filename: "ingestion_summary.json", path: "Tool1/ingestion_summary.json", status: "pending" },
  { toolId: 2, filename: "path_report.json", path: "Tool2/path_report.json", status: "pending" },
  { toolId: 3, filename: "trajectory_forecast.json", path: "Tool3/trajectory_forecast.json", status: "pending" },
  { toolId: 4, filename: "response_plan.json", path: "Tool4/response_plan.json", status: "pending" },
  { toolId: 5, filename: "execution_report.json", path: "Tool5/execution_report.json", status: "pending" },
  { toolId: 6, filename: "status.json", path: "Tool6/status.json", status: "pending" },
];

interface ResultsPanelProps {
  selectedToolId: number | null;
  jsonData: any;
}

export const ResultsPanel = ({ selectedToolId, jsonData }: ResultsPanelProps) => {
  const [activeTab, setActiveTab] = useState("structured");

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">Results View</h2>
          <p className="text-xs text-muted-foreground">Tactical Visualizations</p>
        </div>
        <div className="flex gap-1">
          {resultFiles.map(f => (
            <div key={f.toolId} className={`transition-all duration-300 h-2 w-2 rounded-full ${selectedToolId === f.toolId ? 'bg-primary scale-125' : 'bg-muted'}`} />
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {!selectedToolId ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50">
            <Activity className="h-16 w-16 mb-4" />
            <p>Select a tool to view results</p>
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="px-4 pt-2 border-b border-border/50">
              <TabsList className="w-full">
                <TabsTrigger value="structured" className="flex-1"><TableIcon className="w-3 h-3 mr-2" />Visual</TabsTrigger>
                <TabsTrigger value="raw" className="flex-1"><FileJson className="w-3 h-3 mr-2" />Raw JSON</TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-hidden bg-muted/10">
              <TabsContent value="structured" className="h-full m-0 p-4 overflow-y-auto">
                {jsonData ? (
                  <ToolResultRenderer toolId={selectedToolId} data={jsonData} />
                ) : (
                  <div className="text-center py-10 text-muted-foreground">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 opacity-50" />
                    Waiting for output...
                  </div>
                )}
              </TabsContent>
              <TabsContent value="raw" className="h-full m-0 p-4 overflow-auto">
                <pre className="text-[10px] font-mono whitespace-pre-wrap text-foreground/70">
                  {JSON.stringify(jsonData, null, 2)}
                </pre>
              </TabsContent>
            </div>
          </Tabs>
        )}
      </div>
    </div>
  );
};

const ToolResultRenderer = ({ toolId, data }: { toolId: number, data: any }) => {
  switch (toolId) {
    case 1: return <IngestionSummaryView data={data} />;
    case 2: return <PathReportView data={data} />;
    case 3: return <ForecastView data={data} />;
    case 4: return <ResponsePlanView data={data} />;
    case 5: return <ExecutionReportView data={data} />;
    case 6: return <GovernanceView data={data} />;
    default: return <div className="text-sm">Visualizer not implemented for Tool {toolId}</div>;
  }
}

// --- Tool Visualizers ---

const IngestionSummaryView = ({ data }: { data: any }) => {
  if (!data || !data.total_events) return <div className="text-amber-500 p-4">No Summary Data Available</div>;

  const typeCounts = data.by_type || {};
  // const successRate = (data.success / data.total_events) * 100; // Unused

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-2">
        <Card className="bg-card/50 border-white/10 text-center py-2">
          <div className="text-2xl font-bold">{data.total_events}</div>
          <div className="text-[10px] text-muted-foreground">Total Events</div>
        </Card>
        <Card className="bg-green-500/10 border-green-500/20 text-center py-2">
          <div className="text-2xl font-bold text-green-400">{data.success}</div>
          <div className="text-[10px] text-muted-foreground">Ingested</div>
        </Card>
        <Card className="bg-red-500/10 border-red-500/20 text-center py-2">
          <div className="text-2xl font-bold text-red-400">{data.failed}</div>
          <div className="text-[10px] text-muted-foreground">Rejected</div>
        </Card>
      </div>

      <Card className="bg-card/50 border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Event Type Distribution</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Object.entries(typeCounts).map(([type, count]: [string, any]) => (
            <div key={type} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>{type}</span>
                <span className="text-muted-foreground">{count}</span>
              </div>
              <Progress value={(count / data.total_events) * 100} className="h-1.5" />
            </div>
          ))}
          {Object.keys(typeCounts).length === 0 && (
            <div className="text-xs text-muted-foreground">No distribution data</div>
          )}
        </CardContent>
      </Card>

      <div className="text-[10px] text-muted-foreground text-center">
        Source: {data.source_file}
      </div>
    </div>
  );
}

const PathReportView = ({ data }: { data: any[] }) => {
  if (!Array.isArray(data)) return <div className="text-amber-500 p-4">Invalid Data Format: Expected Array</div>;

  return (
    <div className="space-y-6">
      {data.map((session, idx) => (
        <Card key={idx} className="bg-card/50 border-white/10 overflow-hidden relative">
          <div className={`absolute top-0 bottom-0 left-0 w-1 ${session.path_anomaly_score > 20 ? 'bg-destructive' : 'bg-orange-500'}`} />
          <CardHeader className="pb-2 pt-3 pl-4">
            <div className="flex justify-between items-start">
              <div className="text-xs font-mono text-muted-foreground truncate max-w-[200px]" title={session.session_id}>
                {(!session.session_id || session.session_id === "(None,)") ? "General Session" : session.session_id}
              </div>
              <Badge variant={session.path_anomaly_score > 20 ? "destructive" : "secondary"}>
                Score: {session.path_anomaly_score?.toFixed(2)}
              </Badge>
            </div>
            <div className="text-[10px] text-muted-foreground mt-1 flex items-center gap-2">
              <Database className="h-3 w-3" />
              Origin: {session.root_cause_node?.substring(0, 8)}...
            </div>
          </CardHeader>

          {/* New Tactical Narrative Section */}
          {session.tactical_narrative && (
            <div className="mx-4 mb-2 p-2 bg-primary/5 border border-primary/20 rounded text-[11px] text-primary flex gap-2 items-start">
              <Activity className="h-3 w-3 mt-0.5 shrink-0" />
              <span>{session.tactical_narrative}</span>
            </div>
          )}

          <CardContent className="space-y-5 pt-1 pl-4">
            {/* Blast Radius Section */}
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase font-bold text-muted-foreground/70">Blast Radius Impact</div>
              <div className="flex flex-wrap gap-1.5">
                {session.blast_radius?.map((host: string) => (
                  <Badge key={host} variant="secondary" className="text-[10px] bg-red-500/10 text-red-400 border-red-500/20">
                    <Activity className="h-2 w-2 mr-1" />
                    {host}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Vulnerability Intelligence Context (The "Why") */}
            {session.vulnerability_summary && session.vulnerability_summary.length > 0 ? (
              <div className="space-y-2 p-2 rounded bg-destructive/5 border border-destructive/10">
                <div className="text-[10px] uppercase font-bold text-destructive/80 flex items-center gap-1.5">
                  <Shield className="h-3 w-3" />
                  Vulnerability Intelligence Context
                </div>
                <div className="space-y-1.5">
                  {session.vulnerability_summary.map((vuln: string, i: number) => {
                    const isKev = vuln.includes("[KEV]");
                    return (
                      <div key={i} className={`text-[11px] flex items-center justify-between font-mono p-1 rounded ${isKev ? 'bg-destructive/20 text-destructive' : 'text-foreground/70'}`}>
                        <span className="flex items-center gap-1">
                          {isKev && <Zap className="h-3 w-3 fill-current" />}
                          {vuln.split(" ")[0]}
                        </span>
                        <span className="text-[9px] opacity-70">{vuln.split(" ").slice(1).join(" ")}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 p-2 rounded bg-green-500/5 border border-green-500/10 text-[10px] text-green-400">
                <CheckCircle2 className="h-3 w-3" />
                <span>KEV/CWE Intelligence: No active exploits bound to this session.</span>
              </div>
            )}

            {/* CWE Taxonomy Clusters */}
            {session.cwe_clusters && session.cwe_clusters.length > 0 ? (
              <div className="space-y-1.5">
                <div className="text-[10px] uppercase font-bold text-muted-foreground/70">CWE Weakness Patterns</div>
                <div className="flex flex-wrap gap-1">
                  {session.cwe_clusters.map((cluster: string, i: number) => (
                    <Badge key={i} variant="outline" className="text-[9px] py-0 border-primary/30 text-primary">
                      {cluster}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-[9px] text-muted-foreground italic pl-1 flex items-center gap-1">
                <Database className="h-2 w-2" />
                Heuristic Mapping Active: No high-risk taxonomy clusters found.
              </div>
            )}

            {/* Tactical Event Summary (For large volumes) */}
            {session.event_summary && Object.keys(session.event_summary).length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-white/5">
                <div className="text-[10px] uppercase font-bold text-muted-foreground/70">Tactical Session Summary</div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(session.event_summary).map(([type, count]) => (
                    <Badge key={type} variant="secondary" className="text-[10px] bg-blue-500/5 text-blue-400 border-blue-500/10">
                      {type}: {count as number}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Prediction Vector */}
            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="text-[10px] uppercase font-bold text-muted-foreground/70">AI Prediction Vector</div>
              {session.prediction_vector?.map((pred: any, i: number) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span className="flex items-center gap-1.5 italic text-foreground/80">
                      <ArrowRight className="h-3 w-3 text-primary" />
                      {pred.next_node}
                    </span>
                    <span className="font-mono text-primary font-bold">{(pred.probability * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={pred.probability * 100} className="h-1 bg-primary/20" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

const ForecastView = ({ data }: { data: any[] }) => {
  if (!Array.isArray(data)) return <div className="text-amber-500 p-4">Invalid Data Format: Expected Array</div>;

  return (
    <div className="space-y-6">
      {data.map((model, idx) => {
        const confidence = model.aggregate_confidence;
        return (
          <Card key={idx} className="bg-card/50 border-white/10">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-center">
                <CardTitle className="text-xs font-mono truncate max-w-[180px]" title={model.session_id}>
                  {model.session_id}
                </CardTitle>
                <Badge variant="outline" className={`text-[10px] ${confidence > 0.7 ? 'border-green-500 text-green-400' : 'border-yellow-500 text-yellow-400'}`}>
                  Confidence: {(confidence * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="text-[10px] text-muted-foreground mt-1">
                Model: {model.model_version}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {model.predicted_scenarios?.slice(0, 3).map((sc: any, i: number) => (
                <div key={i} className="space-y-1 border-b border-white/5 pb-2 last:border-0 last:pb-0">
                  <div className="flex justify-between text-xs items-center mb-1">
                    <div className="flex gap-2 items-center">
                      {sc.scenario_type && <Badge variant="outline" className="text-[9px] text-blue-400 border-blue-400/30">{sc.scenario_type}</Badge>}
                      <Badge variant="secondary" className="text-[10px] h-4 px-1">{sc.risk_level}</Badge>
                      <span className="font-mono text-primary font-bold">{(sc.probability * 100).toFixed(0)}%</span>
                    </div>
                    <span className="text-[10px] text-muted-foreground">{sc.reaction_time_window?.min_seconds}-{sc.reaction_time_window?.max_seconds}s</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-[11px]">
                    <Activity className="h-3 w-3 text-muted-foreground" />
                    <span className="font-medium text-foreground/90">
                      {sc.sequence?.join(" → ")}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

const ResponsePlanView = ({ data }: { data: any[] }) => {
  if (!Array.isArray(data)) return <div className="text-amber-500 p-4">Invalid Data Format: Expected Array</div>;

  const sorted = [...data].sort((a, b) => a.priority_rank - b.priority_rank);

  return (
    <div className="grid grid-cols-1 gap-4">
      {sorted.map((plan: any, i: number) => (
        <div key={i} className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <div className="text-xs font-mono text-muted-foreground">{plan.session_id}</div>
            <Badge className={plan.urgency_level === 'Critical' ? 'bg-red-500 hover:bg-red-600' : 'bg-orange-500 hover:bg-orange-600'}>
              Rank #{plan.priority_rank}
            </Badge>
          </div>

          {plan.recommended_actions?.map((action: any, idx: number) => (
            <Card key={idx} className="bg-card/50 border-white/10 relative overflow-hidden group hover:border-primary/30 transition-colors">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
              <CardContent className="p-3">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex flex-col gap-1">
                    <div className="font-semibold text-sm flex items-center gap-2">
                      {action.action_type === 'Block' || action.action_type.includes('Block') ? <Shield className="h-3 w-3 text-red-400" /> : <Zap className="h-3 w-3 text-yellow-400" />}
                      {action.action_type}
                    </div>
                    <div className="flex gap-1">
                      {action.action_class && (
                        <Badge variant={action.action_class === 'Disruptive' ? 'destructive' : 'secondary'} className="text-[9px] px-1 h-4">
                          {action.action_class.toUpperCase()}
                        </Badge>
                      )}
                      {action.requires_approval && (
                        <Badge variant="outline" className="text-[9px] px-1 h-4 text-orange-400 border-orange-400/50">
                          APPROVAL REQ
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="text-[10px] text-muted-foreground">within {action.recommended_within_seconds}s</div>
                </div>

                <div className="bg-white/5 p-2 rounded text-xs text-muted-foreground mb-2 font-mono">
                  {action.justification?.signal_gap_closed || "Risk reduction strategy"}
                </div>

                <div className="flex items-center justify-between text-[10px]">
                  <Badge variant="secondary" className="text-green-400 bg-green-400/10 border-green-400/20">
                    Risk -{(action.justification?.risk_reduction?.absolute * 100).toFixed(0)}%
                  </Badge>
                  <div className="flex items-center gap-1.5 text-muted-foreground bg-white/5 px-2 py-1 rounded">
                    <Database className="h-3 w-3" />
                    Target: {action.target?.identifier || action.target}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ))}
    </div>
  );
};

const ExecutionReportView = ({ data }: { data: any }) => {
  const actions = data.executions || data.executed_actions || [];

  return (
    <div className="space-y-4">
      <div className="flex gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">{data.summary_stats?.success ?? 0}</div>
          <div className="text-[10px] uppercase text-muted-foreground">Success</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-400">{data.summary_stats?.failed ?? 0}</div>
          <div className="text-[10px] uppercase text-muted-foreground">Failed</div>
        </div>
      </div>

      <div className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Execution Log</div>
      {actions.map((act: any, i: number) => (
        <div key={i} className="flex flex-col gap-2 p-3 rounded-lg border border-white/10 bg-card/30">
          <div className="flex items-center gap-3">
            {act.final_status === 'success' || act.status === 'success' ? (
              <div className="h-6 w-6 rounded-full bg-green-500/20 flex items-center justify-center shrink-0">
                <CheckCircle2 className="text-green-500 h-4 w-4" />
              </div>
            ) : (
              <div className="h-6 w-6 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                <XCircle className="text-destructive h-4 w-4" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{act.action_name || act.action}</div>
              <div className="text-xs text-muted-foreground truncate">Target: {act.target}</div>
            </div>
            {act.rollback_token && (
              <Badge variant="outline" className="text-[10px] text-blue-400 border-blue-400/30 flex gap-1 items-center">
                <RefreshCw className="h-3 w-3" />
                Rollback Ready
              </Badge>
            )}
          </div>
          {act.message && (
            <div className="text-[10px] text-muted-foreground ml-9 italic">
              {act.message}
            </div>
          )}
        </div>
      ))}
      {actions.length === 0 && (
        <div className="text-center p-8 border border-dashed border-white/10 rounded-lg text-muted-foreground">
          No actions were executed.
        </div>
      )}
    </div>
  );
};

const GovernanceView = ({ data }: { data: any }) => {
  if (!data || data.error) return <div className="text-red-400 p-4 border border-red-500/20 rounded-lg bg-red-500/5">{data?.error || "Governance Data Unavailable"}</div>;

  const momentum = data.trust_momentum ?? 0;
  const isPositive = momentum > 0;

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-br from-card/50 to-primary/5 border-primary/20">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-sm flex items-center gap-2">
              <Shield className="h-4 w-4 text-primary" />
              Active Trust Model
            </CardTitle>
            <Badge variant="outline" className="font-mono text-[10px]">{data.version_id}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Gauge Visualization */}
          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium">
                <span>Containment Threshold</span>
                <span className="text-primary">{(data.containment_threshold * 100).toFixed(1)}%</span>
              </div>
              <Progress value={data.containment_threshold * 100} className="h-2 bg-secondary" />
              <p className="text-[10px] text-muted-foreground">Below this trust level, hosts are isolated automatically.</p>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium">
                <span>Disruptive Action Threshold</span>
                <span className="text-destructive">{(data.disruptive_threshold * 100).toFixed(1)}%</span>
              </div>
              <Progress value={data.disruptive_threshold * 100} className="h-2 bg-destructive/10" />
              <p className="text-[10px] text-muted-foreground">Above this, risky blocks require approval.</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-white/5 rounded-xl border border-white/5 text-center relative overflow-hidden">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Momentum</div>
              <div className={`text-2xl font-black flex items-center justify-center gap-2 ${isPositive ? 'text-green-400' : 'text-red-400'
                }`}>
                {isPositive ? <ArrowRight className="-rotate-45 h-5 w-5" /> : <ArrowRight className="rotate-45 h-5 w-5" />}
                {Math.abs(momentum).toFixed(4)}
              </div>
              <div className="text-[10px] mt-1 opacity-70">
                {data.trend === 'relaxing' ? 'Adapting (Relaxing)' : 'Hardening (Tightening)'}
              </div>
            </div>
            <div className="p-4 bg-white/5 rounded-xl border border-white/5 text-center">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Stability Streak</div>
              <div className="text-2xl font-black text-blue-400 flex items-center justify-center gap-2">
                <Activity className="h-4 w-4" />
                {data.success_streak ?? 0}
              </div>
              <div className="text-[10px] mt-1 opacity-70">Consecutive Successes</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-start gap-3">
        <div className="bg-blue-500/20 p-1.5 rounded-full shrink-0">
          <Database className="h-3 w-3 text-blue-400" />
        </div>
        <div>
          <h4 className="text-xs font-semibold text-blue-100 mb-0.5">Persistence Active</h4>
          <p className="text-[10px] text-blue-200/70">
            Automated governance learning is persisted in <code>Tool6/data/governance.db</code>.
          </p>
        </div>
      </div>
    </div>
  );
};
