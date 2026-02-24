import { useState, useEffect } from "react";
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
  BookOpen,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Database,
  Terminal,
  ShieldAlert,
  Clock,
  TrendingUp,
  Target
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
  const total = data.total_processed || data.total_events || 0;
  if (!data || total === 0) return <div className="text-amber-500 p-4">No Summary Data Available</div>;

  const intel = data.intelligence || {};
  const vulns = data.vulnerabilities || {};
  const typeCounts = intel.event_types || data.by_type || {};

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-2">
        <Card className="bg-card/50 border-white/10 text-center py-2">
          <div className="text-xl font-bold">{total}</div>
          <div className="text-[9px] text-muted-foreground uppercase">Processed</div>
        </Card>
        <Card className="bg-green-500/10 border-green-500/20 text-center py-2">
          <div className="text-xl font-bold text-green-400">{data.success}</div>
          <div className="text-[9px] text-muted-foreground uppercase">Ingested</div>
        </Card>
        <Card className="bg-red-500/10 border-red-500/20 text-center py-2">
          <div className="text-xl font-bold text-red-400">{data.failed}</div>
          <div className="text-[9px] text-muted-foreground uppercase">Rejected</div>
        </Card>
      </div>


      {/* MITRE & Intelligence Breakdown */}
      <div className="grid grid-cols-2 gap-3">
        <Card className="bg-card/50 border-white/10">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[10px] uppercase text-muted-foreground">Top Hosts</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-1">
            {Object.entries(intel.top_hosts || {}).map(([host, count]: [string, any]) => (
              <div key={host} className="flex justify-between text-[10px] font-mono border-b border-white/5 pb-1 last:border-0">
                <span className="truncate max-w-[80px]">{host}</span>
                <span className="text-primary">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-white/10">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[10px] uppercase text-muted-foreground">Top Users</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-1">
            {Object.entries(intel.top_users || {}).map(([user, count]: [string, any]) => (
              <div key={user} className="flex justify-between text-[10px] font-mono border-b border-white/5 pb-1 last:border-0">
                <span className="truncate max-w-[80px]">{user}</span>
                <span className="text-primary">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* MITRE Techniques */}
      {intel.mitre_breakdown && Object.keys(intel.mitre_breakdown).length > 0 && (
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-[10px] uppercase">MITRE ATT&CK Mapping</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-1">
            <div className="flex flex-wrap gap-2">
              {Object.entries(intel.mitre_breakdown).map(([tid, count]: [string, any]) => (
                <div key={tid} className="flex flex-col items-center bg-white/5 p-1 px-2 rounded border border-white/10 min-w-[50px]">
                  <span className="text-[11px] font-bold text-primary">{tid}</span>
                  <span className="text-[9px] opacity-60">{count} events</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-card/50 border-white/10">
        <CardHeader className="p-3 pb-1">
          <CardTitle className="text-[10px] uppercase">Event Distribution</CardTitle>
        </CardHeader>
        <CardContent className="p-3 pt-1 space-y-2">
          {Object.entries(typeCounts).map(([type, count]: [string, any]) => (
            <div key={type} className="space-y-1">
              <div className="flex justify-between text-[10px]">
                <span>{type}</span>
                <span className="text-muted-foreground">{count}</span>
              </div>
              <Progress value={(count / total) * 100} className="h-1" />
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="text-[9px] text-muted-foreground text-center italic">
        Analyzed {total} lines with a {data.ingestion_limit} line safety limit applied.
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
                    // Improved logic: If it already looks like ID: Name, don't split it into ugly lines
                    const isNewFormat = /^C[WE|VE]-[0-9-]+: /.test(vuln);

                    if (isNewFormat) {
                      return (
                        <div key={i} className={`text-[11px] font-bold p-1.5 rounded flex items-center gap-1.5 ${isKev ? 'bg-destructive/20 text-destructive' : 'bg-white/5 text-foreground/85'}`}>
                          {isKev && <Zap className="h-3 w-3 fill-current" />}
                          {vuln.replace("[KEV]", "").trim()}
                        </div>
                      );
                    }

                    const hasParens = vuln.includes("(");
                    const name = hasParens ? vuln.split("(")[0].trim() : vuln;
                    const details = hasParens ? "(" + vuln.split("(").slice(1).join("(") : "";

                    return (
                      <div key={i} className={`text-[11px] flex flex-col gap-0.5 p-1.5 rounded ${isKev ? 'bg-destructive/20 text-destructive' : 'bg-white/5 text-foreground/80'}`}>
                        <div className="flex items-center gap-1.5 font-bold">
                          {isKev && <Zap className="h-3 w-3 fill-current" />}
                          {name}
                        </div>
                        {details && <div className="text-[9px] opacity-70 font-mono pl-4">{details}</div>}
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
          <Card key={idx} className="bg-card/50 border-white/10 shadow-lg">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-center">
                <CardTitle className="text-xs font-mono font-bold text-primary truncate max-w-[180px]" title={model.session_id}>
                  {model.session_id}
                </CardTitle>
                <Badge variant="outline" className={`text-[10px] px-2 py-0.5 ${confidence > 0.5 ? 'border-green-500 text-green-400 bg-green-500/5' : 'border-yellow-500 text-yellow-400 bg-yellow-500/5'}`}>
                  Confidence: {(confidence * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1.5 font-medium">
                <Shield className="h-3 w-3" />
                Intelligence Model: {model.model_version}
              </div>
            </CardHeader>

            {/* Strategic Mentor Insight */}
            {model.mentor_narrative && (
              <div className="mx-4 mb-2 p-2.5 bg-primary/10 border border-primary/20 rounded-md text-[11px] text-primary/95 leading-relaxed flex gap-2 items-start shadow-inner">
                <Activity className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                <span className="font-medium italic">{model.mentor_narrative}</span>
              </div>
            )}

            <CardContent className="space-y-4 pt-2">
              <div className="text-[10px] uppercase font-bold text-muted-foreground/50 tracking-wider px-1">Forecasted Attack Path</div>
              {model.predicted_scenarios?.slice(0, 3).map((sc: any, i: number) => (
                <div key={i} className="group space-y-2 p-3 rounded-lg bg-white/5 border border-white/5 hover:border-primary/30 hover:bg-white/[0.08] transition-all">
                  <div className="flex justify-between text-xs items-center">
                    <div className="flex gap-2 items-center">
                      <Badge variant="outline" className={`text-[9px] uppercase tracking-tighter ${sc.scenario_type === 'Primary' ? 'text-blue-400 border-blue-400/30 bg-blue-400/5' : 'text-muted-foreground border-white/10'}`}>
                        {sc.scenario_type || 'Potential'}
                      </Badge>
                      <Badge variant="secondary" className={`text-[10px] h-4 px-1.5 font-bold ${sc.risk_level === 'High' || sc.risk_level === 'Critical' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                        {sc.risk_level}
                      </Badge>
                      <span className="font-mono text-primary font-black ml-1">{(sc.probability * 100).toFixed(0)}%</span>
                    </div>
                    <Badge variant="outline" className="text-[10px] text-muted-foreground font-mono bg-black/20 border-white/5">
                      {sc.time_window_text || `${sc.reaction_time_window?.min_seconds}-${sc.reaction_time_window?.max_seconds}s`}
                    </Badge>
                  </div>

                  <div className="flex items-start gap-2 text-[12px] bg-black/20 p-2 rounded border border-white/5">
                    <Zap className="h-3.5 w-3.5 text-primary mt-0.5 shrink-0" />
                    <span className="font-semibold text-foreground/90 tracking-tight">
                      {sc.human_readable_sequence || sc.sequence?.join(" → ")}
                    </span>
                  </div>

                  {/* Explainability Snippet if available */}
                  {sc.explainability?.positive_evidence?.[0] && (
                    <div className="text-[9px] text-muted-foreground/60 italic pl-6">
                      Evidence: {sc.explainability.positive_evidence[0]}
                    </div>
                  )}
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
    <div className="grid grid-cols-1 gap-6">
      {sorted.map((plan: any, i: number) => (
        <div key={i} className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <div className="text-xs font-mono font-bold text-primary">{plan.session_id}</div>
            <Badge className={plan.urgency_level === 'Critical' ? 'bg-red-500 hover:bg-red-600' : 'bg-orange-500 hover:bg-orange-600'}>
              Urgency: {plan.urgency_level}
            </Badge>
          </div>

          {/* Strategic Decision Insight */}
          {plan.mentor_summary && (
            <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-md text-[11px] text-cyan-100 italic leading-relaxed flex gap-2 items-start">
              <Shield className="h-3.5 w-3.5 mt-0.5 shrink-0 text-cyan-400" />
              <span>{plan.mentor_summary}</span>
            </div>
          )}

          {plan.recommended_actions?.map((action: any, idx: number) => (
            <Card key={idx} className="bg-card/50 border-white/10 relative overflow-hidden group hover:border-primary/30 transition-all shadow-md">
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

                {/* Mitigation Guidelines */}
                {action.mitigation_guidelines && action.mitigation_guidelines.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-white/5 space-y-1.5">
                    <div className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest pl-1">Mitigation Guidelines</div>
                    <div className="space-y-1">
                      {action.mitigation_guidelines.map((g: string, k: number) => (
                        <div key={k} className="flex gap-2 text-[10px] leading-relaxed text-foreground/80">
                          <span className="text-primary mt-1">•</span>
                          <span>{g}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ))}
    </div>
  );
};

const ExecutionReportView = ({ data }: { data: any }) => {
  const [scriptInfo, setScriptInfo] = useState<any>(null);
  const [loadingScript, setLoadingScript] = useState(true);

  // Fetch latest script info from backend
  const fetchScriptInfo = async () => {
    setLoadingScript(true);
    try {
      const res = await fetch("http://localhost:8000/api/tool5/script-info");
      const info = await res.json();
      setScriptInfo(info);
    } catch {
      setScriptInfo({ available: false, message: "Backend unavailable." });
    } finally {
      setLoadingScript(false);
    }
  };

  useEffect(() => { fetchScriptInfo(); }, []);

  const handleDownload = () => {
    if (!scriptInfo?.path) return;
    const url = `http://localhost:8000/api/download?path=${encodeURIComponent(scriptInfo.path)}`;
    const a = document.createElement("a");
    a.href = url;
    a.download = scriptInfo.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Support both old format (executions) and new format (actions_included)
  const actions = data.actions_included || data.executions || [];
  const totalActions = data.total_actions ?? actions.length;
  const stagedCount = data.staged_count ?? 0;
  const networkActions = actions.filter((a: any) => a.domain === "Network" || a.execution_mode === "staged");
  const endpointActions = actions.filter((a: any) => a.domain === "Endpoint");
  const scriptFilename = data.script_filename || scriptInfo?.filename;

  return (
    <div className="space-y-6">

      {/* ── Header Banner ─────────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-xl border border-cyan-500/30 bg-gradient-to-br from-cyan-950/60 via-slate-900/80 to-slate-900/60 p-5 shadow-lg shadow-cyan-500/5">
        <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="relative flex items-start gap-4">
          <div className="h-12 w-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
            <Terminal className="h-6 w-6 text-cyan-400" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1">Tool 5 — Remediation Script Generator</div>
            <div className="text-sm text-white/80 leading-relaxed">
              No commands were executed automatically. Tool 5 analysed the AI decisions from Tool 4 and generated a
              <span className="text-cyan-300 font-semibold"> ready-to-run PowerShell script</span> tailored to the exact threats detected.
              Download it, review it, and run it as Administrator.
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats Row ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-3">
        <Card className="p-3 bg-slate-900/60 border-white/10 text-center">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Total Actions</div>
          <div className="text-2xl font-mono font-black text-white">{totalActions}</div>
          <div className="text-[9px] text-muted-foreground mt-0.5">in script</div>
        </Card>
        <Card className="p-3 bg-yellow-500/5 border-yellow-500/20 text-center">
          <div className="text-[10px] font-bold text-yellow-400 uppercase tracking-widest mb-1">Needs Approval</div>
          <div className="text-2xl font-mono font-black text-yellow-300">{stagedCount}</div>
          <div className="text-[9px] text-yellow-500/70 mt-0.5">flagged in script</div>
        </Card>
        <Card className="p-3 bg-cyan-500/5 border-cyan-500/20 text-center">
          <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-1">Web Guidelines</div>
          <div className="text-2xl font-mono font-black text-cyan-300">{data.web_count || 0}</div>
          <div className="text-[9px] text-cyan-500/70 mt-0.5">manual response plans</div>
        </Card>
        <Card className="p-3 bg-green-500/5 border-green-500/20 text-center">
          <div className="text-[10px] font-bold text-green-400 uppercase tracking-widest mb-1">Status</div>
          <div className="text-sm font-bold text-green-300 mt-1">Ready</div>
          <div className="text-[9px] text-green-500/70 mt-0.5">awaiting deploy</div>
        </Card>
      </div>

      {/* ── Download Card ─────────────────────────────────────────────── */}
      <Card className="border-green-500/30 bg-gradient-to-r from-green-950/50 to-slate-900/60 shadow-lg shadow-green-500/5">
        <CardContent className="p-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center shrink-0">
                  <Shield className="h-5 w-5 text-green-400" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">
                    Remediation Package Ready
                  </div>
                  <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                    {data.script_filename} & {data.guideline_filename}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                className="h-8 text-xs bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-4 gap-2"
                disabled={!data.guideline_path}
                onClick={() => {
                  const url = `http://localhost:8000/api/download?path=${encodeURIComponent(data.guideline_path)}`;
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = data.guideline_filename;
                  a.click();
                }}
              >
                <BookOpen className="h-3.5 w-3.5" />
                Get Web Guidelines
              </Button>
              <Button
                size="sm"
                className="h-8 text-xs bg-green-600 hover:bg-green-500 text-white font-bold px-4 gap-2"
                disabled={!data.script_path}
                onClick={() => {
                  const url = `http://localhost:8000/api/download?path=${encodeURIComponent(data.script_path)}`;
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = data.script_filename;
                  a.click();
                }}
              >
                <Database className="h-3.5 w-3.5" />
                Download Script
              </Button>
            </div>
          </div>

          {/* How to run instructions */}
          <div className="mt-4 p-3 bg-black/30 rounded-lg border border-white/5 text-[10px] font-mono text-muted-foreground space-y-1">
            <div className="text-white/50 font-bold uppercase tracking-widest text-[9px] mb-2">How to Run</div>
            <div><span className="text-cyan-400">1.</span> Open <span className="text-white">PowerShell</span> as <span className="text-yellow-400">Administrator</span></div>
            <div><span className="text-cyan-400">2.</span> Navigate to the downloads folder</div>
            <div><span className="text-cyan-400">3.</span> Run: <span className="text-green-400">.\ {scriptFilename || "PredictPath_Remediation_*.ps1"}</span></div>
            <div><span className="text-cyan-400">4.</span> Review each <span className="text-yellow-400"># ROLLBACK:</span> comment to undo any change</div>
          </div>
        </CardContent>
      </Card>

      {/* ── Action Breakdown ──────────────────────────────────────────── */}
      {actions.length > 0 && (
        <div className="space-y-3">
          <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
            <Activity className="h-3 w-3" />
            Script Contents — Action Breakdown
          </div>

          {/* Network Section */}
          {actions.filter((a: any) => a.domain === "Network").length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 px-1">
                <div className="h-1.5 w-1.5 rounded-full bg-green-400" />
                <span className="text-[10px] font-bold text-green-400 uppercase tracking-widest">Section 1 — Network Mitigations</span>
              </div>
              {actions.filter((a: any) => a.domain === "Network").map((act: any, i: number) => (
                <ActionCard key={i} act={act} index={i} />
              ))}
            </div>
          )}

          {/* Endpoint Section */}
          {actions.filter((a: any) => a.domain === "Endpoint").length > 0 && (
            <div className="space-y-2 mt-4">
              <div className="flex items-center gap-2 px-1">
                <div className="h-1.5 w-1.5 rounded-full bg-yellow-400" />
                <span className="text-[10px] font-bold text-yellow-400 uppercase tracking-widest">Section 2 — Endpoint Mitigations</span>
              </div>
              {actions.filter((a: any) => a.domain === "Endpoint").map((act: any, i: number) => (
                <ActionCard key={i} act={act} index={i} />
              ))}
            </div>
          )}

          {/* Web Section */}
          {actions.filter((a: any) => a.domain === "Web").length > 0 && (
            <div className="space-y-2 mt-4">
              <div className="flex items-center gap-2 px-1">
                <div className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">Section 3 — Web & Cloud Mitigations</span>
              </div>
              {actions.filter((a: any) => a.domain === "Web").map((act: any, i: number) => (
                <ActionCard key={i} act={act} index={i} />
              ))}
            </div>
          )}

          {/* Old format fallback */}
          {actions.filter((a: any) => !a.domain).map((act: any, i: number) => (
            <ActionCard key={i} act={act} index={i} />
          ))}
        </div>
      )}

      {actions.length === 0 && (
        <div className="text-center p-12 bg-white/5 border border-dashed border-white/10 rounded-xl">
          <ShieldAlert className="h-8 w-8 text-white/20 mx-auto mb-3" />
          <div className="text-sm font-medium text-muted-foreground tracking-tight">No Actions Generated</div>
          <div className="text-[10px] text-muted-foreground/60 mt-1 uppercase tracking-widest">Run Tool 5 to generate a remediation script</div>
        </div>
      )}
    </div>
  );
};

const ActionCard = ({ act, index }: { act: any; index: number }) => {
  const isApproval = act.requires_approval || act.execution_mode === "staged" || act.final_status === "pending";
  const domain = act.domain || (act.execution_mode === "auto" ? "Endpoint" : "Network");
  const domainColor = domain === "Network" ? "text-green-400 border-green-500/20 bg-green-500/5" : "text-yellow-400 border-yellow-500/20 bg-yellow-500/5";
  const urgency = act.urgency || act.urgency_level || "Unknown";

  return (
    <Card className={`border-white/5 bg-card/40 overflow-hidden transition-all hover:border-primary/20 ${isApproval ? "border-l-2 border-l-yellow-500/50" : ""}`}>
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 border ${isApproval ? "bg-yellow-500/10 border-yellow-500/20" : "bg-green-500/10 border-green-500/20"}`}>
            {isApproval
              ? <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />
              : <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
            }
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-white">{act.action_type || act.action_name || act.action}</span>
              <Badge variant="outline" className={`text-[9px] py-0 px-1.5 ${domainColor}`}>{domain}</Badge>
              {isApproval && (
                <Badge variant="outline" className="text-[9px] py-0 px-1.5 text-yellow-400 border-yellow-500/30 bg-yellow-500/5">
                  ⚠ APPROVAL REQUIRED
                </Badge>
              )}
              {(urgency === "Critical" || urgency === "High") && (
                <Badge variant="outline" className="text-[9px] py-0 px-1.5 text-red-400 border-red-500/30 bg-red-500/5">
                  {urgency}
                </Badge>
              )}
            </div>
            <div className="text-[10px] text-muted-foreground font-mono mt-1">
              Target: <span className="text-primary/80">{act.target}</span>
              {act.session_id && <> · Session: <span className="text-white/50">{act.session_id}</span></>}
            </div>
            {act.mentor_context && (
              <div className="mt-2 text-[10px] text-cyan-300/70 italic border-l border-cyan-500/20 pl-2">
                {act.mentor_context}
              </div>
            )}

            {act.mitigation_guidelines && act.mitigation_guidelines.length > 0 && (
              <div className="mt-2 space-y-1">
                <div className="text-[9px] font-bold text-white/40 uppercase tracking-widest">Tactical Guidelines</div>
                <div className="space-y-1 pl-1">
                  {act.mitigation_guidelines.map((g: string, i: number) => (
                    <div key={i} className="flex items-start gap-1.5 text-[10px] text-white/70">
                      <span className="text-cyan-500 mt-1">•</span>
                      <span>{g}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};



const GovernanceView = ({ data: initialData }: { data: any }) => {
  const [data, setData] = useState<any>(initialData);
  const [loading, setLoading] = useState(false);

  const fetchLive = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/tool6/status");
      const live = await res.json();
      setData(live);
    } catch {
      // keep existing data
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLive(); }, []);

  // Sync with prop updates from pipeline
  useEffect(() => {
    if (initialData && !initialData.error) {
      setData(initialData);
    }
  }, [initialData]);

  if (!data || data.error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
            <Database className="h-3 w-3" />
            Governance Engine
          </div>
          <Button size="sm" variant="outline" className="h-7 text-xs border-white/10" onClick={fetchLive}>
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
        <div className="text-center p-12 bg-white/5 border border-dashed border-white/10 rounded-xl">
          <Database className="h-8 w-8 text-white/20 mx-auto mb-3" />
          <div className="text-sm font-medium text-muted-foreground">Governance Database Not Ready</div>
          <div className="text-[10px] text-muted-foreground/60 mt-1 uppercase tracking-widest">
            {data?.error || "Run Tool 6 to initialise the governance engine"}
          </div>
        </div>
      </div>
    );
  }

  const momentum = data.trust_momentum ?? 0;
  const isPositive = momentum > 0;
  const isNeutral = Math.abs(momentum) <= 0.001;
  const containPct = (data.containment_threshold ?? 0.6) * 100;
  const disruptPct = (data.disruptive_threshold ?? 0.85) * 100;
  const ledgerEntries = data.recent_ledger_entries || [];
  const modelHistory = data.model_history || [];
  const lastEvent = data.last_learning_event;

  const momentumColor = isNeutral ? "text-white/60" : isPositive ? "text-green-400" : "text-red-400";
  const momentumBg = isNeutral ? "bg-white/5 border-white/10" : isPositive ? "bg-green-500/5 border-green-500/20" : "bg-red-500/5 border-red-500/20";

  return (
    <div className="space-y-5">

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Shield className="h-4 w-4 text-primary" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Governance & Learning Engine</div>
            <div className="text-[10px] text-muted-foreground font-mono">
              Model: <span className="text-primary">{data.version_id || "—"}</span>
              {data.source === "status_file" && <span className="ml-2 text-green-400/60">· live</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            className="h-7 text-xs bg-cyan-600 hover:bg-cyan-500 text-white font-bold gap-1.5"
            disabled={!data.pdf_audit_path && !data.last_learning_event?.pdf_audit_path}
            onClick={() => {
              const path = data.pdf_audit_path || data.last_learning_event?.pdf_audit_path;
              const filename = data.pdf_audit_filename || data.last_learning_event?.pdf_audit_filename || "Audit_Report.pdf";
              const url = `http://localhost:8000/api/download?path=${encodeURIComponent(path)}`;
              const a = document.createElement("a");
              a.href = url;
              a.download = filename;
              a.click();
            }}
          >
            <BookOpen className="h-3 w-3" />
            Audit PDF
          </Button>
          {data.ledger_integrity !== undefined && (
            <Badge variant="outline" className={`text-[9px] py-0 px-1.5 ${data.ledger_integrity ? "text-green-400 border-green-500/30 bg-green-500/5" : "text-red-400 border-red-500/30 bg-red-500/5"}`}>
              {data.ledger_integrity ? "✓ Ledger Verified" : "⚠ Tampered"}
            </Badge>
          )}
          <Button size="sm" variant="outline" className="h-7 text-xs border-white/10" onClick={fetchLive}>
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* ── Drift Alerts ─────────────────────────────────────────────── */}
      {data.drift_alerts && data.drift_alerts.length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] font-bold text-yellow-400 uppercase tracking-widest flex items-center gap-2">
            <AlertTriangle className="h-3 w-3" />
            System Drift Alerts
          </div>
          {data.drift_alerts.map((alert: string, i: number) => (
            <div
              key={i}
              className="flex items-start gap-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/25 text-[11px] text-yellow-200"
            >
              <AlertTriangle className="h-3.5 w-3.5 text-yellow-400 shrink-0 mt-0.5" />
              <span>{alert}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Trust Thresholds ────────────────────────────────────────── */}
      <Card className="bg-gradient-to-br from-card/60 to-primary/5 border-primary/15">

        <CardContent className="p-4 space-y-4">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-3">Trust Thresholds</div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Containment Threshold</span>
              <span className="font-mono font-bold text-primary">{containPct.toFixed(1)}%</span>
            </div>
            <div className="relative h-2.5 bg-white/5 rounded-full overflow-hidden">
              <div
                className="absolute left-0 top-0 h-full bg-gradient-to-r from-primary/60 to-primary rounded-full transition-all duration-700"
                style={{ width: `${containPct}%` }}
              />
            </div>
            <p className="text-[9px] text-muted-foreground/60">Below this trust level → automatic host isolation</p>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Disruptive Action Threshold</span>
              <span className="font-mono font-bold text-destructive">{disruptPct.toFixed(1)}%</span>
            </div>
            <div className="relative h-2.5 bg-white/5 rounded-full overflow-hidden">
              <div
                className="absolute left-0 top-0 h-full bg-gradient-to-r from-destructive/50 to-destructive/80 rounded-full transition-all duration-700"
                style={{ width: `${disruptPct}%` }}
              />
            </div>
            <p className="text-[9px] text-muted-foreground/60">Above this → risky blocks require manual approval</p>
          </div>
        </CardContent>
      </Card>

      {/* ── Momentum + Streak ───────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-3">
        <Card className={`col-span-2 p-3 ${momentumBg} border`}>
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">Trust Momentum</div>
          <div className={`text-2xl font-black font-mono flex items-center gap-2 ${momentumColor}`}>
            {isNeutral
              ? <span className="text-lg">→</span>
              : isPositive
                ? <ArrowRight className="-rotate-45 h-5 w-5" />
                : <ArrowRight className="rotate-45 h-5 w-5" />
            }
            {momentum >= 0 ? "+" : ""}{momentum.toFixed(4)}
          </div>
          <div className="text-[10px] mt-1 text-muted-foreground">{data.trend_label || "Unknown"}</div>
        </Card>

        <div className="space-y-2">
          <Card className="p-3 bg-green-500/5 border-green-500/20 text-center">
            <div className="text-[9px] font-bold text-green-400 uppercase tracking-widest">Successes</div>
            <div className="text-xl font-black text-green-300 font-mono">{data.success_streak ?? 0}</div>
            <div className="text-[9px] text-muted-foreground">streak</div>
          </Card>
          <Card className="p-3 bg-red-500/5 border-red-500/20 text-center">
            <div className="text-[9px] font-bold text-red-400 uppercase tracking-widest">Failures</div>
            <div className="text-xl font-black text-red-300 font-mono">{data.failure_streak ?? 0}</div>
            <div className="text-[9px] text-muted-foreground">streak</div>
          </Card>
        </div>
      </div>

      {/* ── Last Learning Event ─────────────────────────────────────── */}
      {lastEvent && (
        <Card className="border-cyan-500/20 bg-cyan-500/5">
          <CardContent className="p-3">
            <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 flex items-center gap-1.5">
              <Activity className="h-3 w-3" />
              Last Learning Event
            </div>
            <div className="text-xs text-white/80 italic leading-relaxed mb-2">
              {lastEvent.narrative || "No narrative available."}
            </div>
            <div className="flex flex-wrap gap-2 text-[9px] font-mono text-muted-foreground">
              {lastEvent.actions_processed != null && (
                <span className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">
                  {lastEvent.actions_processed} actions
                </span>
              )}
              {lastEvent.domains_covered?.map((d: string) => (
                <span key={d} className="px-1.5 py-0.5 bg-primary/10 rounded border border-primary/20 text-primary/80">{d}</span>
              ))}
              {lastEvent.high_urgency_count > 0 && (
                <span className="px-1.5 py-0.5 bg-red-500/10 rounded border border-red-500/20 text-red-400">
                  {lastEvent.high_urgency_count} high urgency
                </span>
              )}
              {lastEvent.is_script_gen && (
                <span className="px-1.5 py-0.5 bg-blue-500/10 rounded border border-blue-500/20 text-blue-400">
                  script-gen source
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Model Version History ───────────────────────────────────── */}
      {modelHistory.length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
            <TrendingUp className="h-3 w-3" />
            Model Version History
          </div>
          <div className="space-y-1.5">
            {modelHistory.map((m: any, i: number) => (
              <div
                key={m.version_id}
                className={`flex items-center gap-3 p-2 rounded-lg border text-[10px] font-mono transition-all
                  ${m.is_active
                    ? "bg-primary/10 border-primary/30 text-white"
                    : "bg-white/2 border-white/5 text-muted-foreground"
                  }`}
              >
                <div className={`h-2 w-2 rounded-full shrink-0 ${m.is_active ? "bg-primary animate-pulse" : "bg-white/20"}`} />
                <span className="flex-1 truncate">{m.version_id}</span>
                <span className={m.trust_momentum >= 0 ? "text-green-400" : "text-red-400"}>
                  {m.trust_momentum >= 0 ? "+" : ""}{(m.trust_momentum ?? 0).toFixed(3)}
                </span>
                <span className="text-muted-foreground/50">
                  {m.containment_threshold != null ? `C:${(m.containment_threshold * 100).toFixed(0)}%` : ""}
                </span>
                {m.is_active && <Badge className="text-[8px] py-0 px-1 bg-primary/20 text-primary border-0">ACTIVE</Badge>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Trust Ledger Audit Trail ────────────────────────────────── */}
      {ledgerEntries.length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
            <Lock className="h-3 w-3" />
            Blockchain Trust Ledger
            <Badge variant="outline" className="text-[8px] py-0 px-1 border-white/10 text-muted-foreground font-mono">
              {data.ledger_entry_count ?? ledgerEntries.length} entries
            </Badge>
          </div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {ledgerEntries.map((entry: any, i: number) => {
              const isLearning = entry.event_type === "LEARNING_UPDATE";
              const isIngest = entry.event_type === "INGEST_REPORT";
              return (
                <div key={i} className="flex items-start gap-2 p-2 bg-white/2 border border-white/5 rounded-lg text-[9px] font-mono">
                  <div className={`h-1.5 w-1.5 rounded-full mt-1 shrink-0 ${isLearning ? "bg-primary" : isIngest ? "bg-cyan-400" : "bg-white/30"
                    }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-bold ${isLearning ? "text-primary/80" : isIngest ? "text-cyan-400/80" : "text-white/50"}`}>
                        {entry.event_type}
                      </span>
                      <span className="text-white/30">{entry.actor}</span>
                      <span className="text-white/20 ml-auto">{entry.hash_id}</span>
                    </div>
                    {entry.payload?.reason && (
                      <div className="text-white/40 mt-0.5 truncate">{entry.payload.reason}</div>
                    )}
                    {entry.payload?.report_id && (
                      <div className="text-white/40 mt-0.5">report: {entry.payload.report_id}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Persistence Notice ──────────────────────────────────────── */}
      <div className="p-3 bg-blue-500/5 border border-blue-500/15 rounded-lg flex items-start gap-2.5">
        <div className="h-6 w-6 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 mt-0.5">
          <Database className="h-3 w-3 text-blue-400" />
        </div>
        <div>
          <div className="text-[10px] font-semibold text-blue-300 mb-0.5">Persistent Governance Active</div>
          <p className="text-[9px] text-blue-200/50 leading-relaxed">
            All trust decisions are persisted in <code className="text-blue-300/70">Tool6/data/governance.db</code> with a tamper-evident blockchain ledger.
            The model self-adjusts thresholds after each pipeline run.
          </p>
        </div>
      </div>
    </div>
  );
};
