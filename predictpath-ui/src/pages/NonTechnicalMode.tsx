import { useState, useCallback, useEffect } from "react";
import { CockpitHeader } from "@/components/cockpit/CockpitHeader";
import { TerminalPanel, TerminalLine } from "@/components/cockpit/TerminalPanel";
import { ResetLevel } from "@/components/cockpit/ResetControls";
import { FolderOpen, Folder, Download, FileText, Clock, Network, Globe, Shield, Play, Trash2, Square } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";

const WS_BASE = "ws://localhost:8000";
const API_BASE = "http://localhost:8000";

interface ScanLog {
    id: string;
    scan_type: string;
    timestamp: string;
    status: "completed" | "failed";
    log_path: string;
    file_name: string;
}

const NonTechnicalMode = () => {
    const [activeScan, setActiveScan] = useState<string | null>(null);
    const [systemStatus, setSystemStatus] = useState<"idle" | "running" | "error">("idle");
    const [logRefreshTrigger, setLogRefreshTrigger] = useState(0);
    const [showLogsDialog, setShowLogsDialog] = useState(false);
    const [logs, setLogs] = useState<ScanLog[]>([]);

    // User prompt state for two-stage workflow (OpenVAS)
    const [showUserPrompt, setShowUserPrompt] = useState(false);
    const [promptMessage, setPromptMessage] = useState("");
    const [currentWebSocket, setCurrentWebSocket] = useState<WebSocket | null>(null);

    // URL Prompt state for Web Scan
    const [showUrlDialog, setShowUrlDialog] = useState(false);
    const [targetUrl, setTargetUrl] = useState("https://example.com");

    // Terminal state
    const [terminalLines, setTerminalLines] = useState<TerminalLine[]>([
        {
            id: "init-1",
            type: "info",
            content: "PredictPath AI - Non-Technical Security Scanner",
            timestamp: new Date(),
        },
        {
            id: "init-2",
            type: "info",
            content: "Select a security scanner to begin guided analysis",
            timestamp: new Date(),
        },
    ]);

    // Fetch logs when dialog opens or refresh trigger changes
    useEffect(() => {
        if (showLogsDialog || logRefreshTrigger > 0) {
            fetchLogs();
        }
    }, [showLogsDialog, logRefreshTrigger]);

    const fetchLogs = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/scans/history`);
            if (res.ok) {
                const data = await res.json();
                setLogs(data.scans || []);
            }
        } catch (error) {
            console.error("Failed to fetch scan history:", error);
        }
    };

    // Add line to terminal
    const addTerminalLine = useCallback(
        (type: TerminalLine["type"], content: string) => {
            const newLine: TerminalLine = {
                id: `line-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                type,
                content,
                timestamp: new Date(),
            };
            setTerminalLines((prev) => [...prev, newLine]);
        },
        []
    );

    // Clear terminal
    const handleClearTerminal = useCallback(() => {
        setTerminalLines([
            {
                id: `clear-${Date.now()}`,
                type: "info",
                content: "Terminal cleared",
                timestamp: new Date(),
            },
        ]);
    }, []);

    // Handle scan start
    const handleScanStart = useCallback(
        (scanType: "network" | "web" | "endpoint") => {
            // Intercept Web scan to ask for URL
            if (scanType === "web") {
                setShowUrlDialog(true);
                return;
            }
            startScanExecution(scanType);
        },
        []
    );

    const startScanExecution = (scanType: string, extraData: any = {}) => {
        setActiveScan(scanType);
        setSystemStatus("running");
        addTerminalLine("command", `# Starting ${scanType.toUpperCase()} Security Scan...`);
        addTerminalLine("info", `Initializing ${scanType} scanner...`);

        const ws = new WebSocket(`${WS_BASE}/ws/scan`);

        ws.onopen = () => {
            ws.send(JSON.stringify({ scan_type: scanType, ...extraData }));
        };

        ws.onmessage = (event) => {
            const msg = event.data;

            // Check if message is JSON (user prompt)
            try {
                const jsonData = JSON.parse(msg);
                console.log("[DEBUG] Parsed JSON message:", jsonData); // Debug log
                if (jsonData.type === "user_prompt") {
                    console.log("[DEBUG] User prompt detected! Showing dialog..."); // Debug log
                    // Show user prompt dialog
                    setPromptMessage(jsonData.message);
                    setShowUserPrompt(true);
                    setCurrentWebSocket(ws);
                    return;
                }
            } catch (e) {
                // Not JSON, treat as regular text message
                // console.log("[DEBUG] Not JSON, treating as text:", msg); // Uncomment for verbose debugging
            }

            let type: TerminalLine["type"] = "info";

            if (msg.includes("Error") || msg.includes("Failed")) type = "error";
            if (msg.includes("Success") || msg.includes("Complete")) type = "success";
            if (msg.startsWith(">")) type = "command";

            addTerminalLine(type, msg.trim());
        };

        ws.onclose = () => {
            setActiveScan(null);
            setSystemStatus("idle");
            addTerminalLine("success", `${scanType.toUpperCase()} scan completed successfully`);
            addTerminalLine("info", "Log file generated and ready for analysis");

            // Trigger log panel refresh
            setLogRefreshTrigger((prev) => prev + 1);
        };

        ws.onerror = () => {
            addTerminalLine("error", "WebSocket Error: Failed to connect to scanner backend");
            setActiveScan(null);
            setSystemStatus("error");
        };
    };

    const handleWebScanSubmit = () => {
        setShowUrlDialog(false);
        if (!targetUrl) {
            addTerminalLine("error", "Error: No target URL provided.");
            return;
        }
        startScanExecution("web", { target_url: targetUrl });
    };

    // Handle stop scan
    const handleStopScan = useCallback(async () => {
        if (!confirm("Are you sure you want to stop the scan?")) return;

        addTerminalLine("command", "# Stopping active scan...");
        try {
            const res = await fetch(`${API_BASE}/api/stop-scan`, { method: "POST" });
            const data = await res.json();
            if (res.ok) {
                addTerminalLine("info", "Stop command sent. Waiting for cleanup...");
            } else {
                addTerminalLine("error", `Failed to stop: ${data.message}`);
            }
        } catch (e) {
            addTerminalLine("error", "Failed to communicate with backend.");
        }
    }, [addTerminalLine]);

    // Handle reset
    const handleReset = useCallback(
        async (level: ResetLevel) => {
            setTerminalLines([
                {
                    id: `reset-${Date.now()}`,
                    type: "command",
                    content: `# Initiating ${level.toUpperCase()} reset...`,
                    timestamp: new Date(),
                },
            ]);

            if (level === "soft" || level === "hard" || level === "logs") {
                try {
                    const res = await fetch(`${API_BASE}/api/reset`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ type: level }),
                    });
                    const data = await res.json();
                    if (res.ok) {
                        addTerminalLine("success", `Reset complete: ${data.deleted.join(", ")}`);
                        setLogRefreshTrigger((prev) => prev + 1);
                    } else {
                        addTerminalLine("error", `Reset Failed: ${data.detail}`);
                    }
                } catch (e) {
                    addTerminalLine("error", "Backend Connection Failed for Reset");
                }
            }
        },
        [addTerminalLine]
    );

    const handleSyncIntel = useCallback(() => {
        addTerminalLine("command", "# Initiating Manual Vulnerability Intelligence Sync...");
        addTerminalLine("info", "[VulnIntel] Connecting to synchronization engine...");

        setSystemStatus("running");

        const ws = new WebSocket(`${WS_BASE}/ws/sync-vuln`);

        ws.onopen = () => {
            ws.send(JSON.stringify({ force: true }));
        };

        ws.onmessage = (event) => {
            const msg = event.data;
            let type: TerminalLine["type"] = "info";
            if (msg.includes("Error") || msg.includes("Failed")) type = "error";
            if (msg.includes("Success") || msg.includes("Complete") || msg.includes("✅")) type = "success";

            addTerminalLine(type, msg.trim());
        };

        ws.onclose = () => {
            setSystemStatus("idle");
            addTerminalLine("success", "[VulnIntel] Sync session closed.");
        };

        ws.onerror = (err) => {
            addTerminalLine("error", "[VulnIntel] Connection failed.");
            setSystemStatus("error");
        };
    }, [addTerminalLine]);

    const handleDownload = async (log: ScanLog) => {
        try {
            const res = await fetch(`${API_BASE}/api/file?path=${encodeURIComponent(log.log_path)}`);
            if (res.ok) {
                const data = await res.json();
                const blob = new Blob([data.content], { type: "text/plain" });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = log.file_name;
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error("Failed to download file:", error);
        }
    };

    const handleDelete = async (log: ScanLog) => {
        if (!confirm(`Delete ${log.file_name}?\n\nThis action cannot be undone.`)) {
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/api/file?path=${encodeURIComponent(log.log_path)}`, {
                method: "DELETE"
            });

            if (res.ok) {
                // Refresh logs list
                fetchLogs();
                addTerminalLine("success", `Deleted ${log.file_name}`);
            } else {
                const data = await res.json();
                addTerminalLine("error", `Failed to delete: ${data.detail}`);
            }
        } catch (error) {
            console.error("Failed to delete file:", error);
            addTerminalLine("error", "Failed to delete file");
        }
    };

    // Handle user prompt response (Yes/No for OpenVAS)
    const handleUserPromptResponse = (choice: "yes" | "no") => {
        if (currentWebSocket && currentWebSocket.readyState === WebSocket.OPEN) {
            // Send user choice back to backend
            currentWebSocket.send(JSON.stringify({ choice }));
            addTerminalLine("command", `> User selected: ${choice.toUpperCase()}`);
        }
        setShowUserPrompt(false);
        setCurrentWebSocket(null);
    };

    const getScanTypeColor = (type: string) => {
        switch (type.toLowerCase()) {
            case "network":
                return "bg-cyan-500/20 text-cyan-400 border-cyan-500/30";
            case "web":
                return "bg-purple-500/20 text-purple-400 border-purple-500/30";
            case "endpoint":
                return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
            default:
                return "bg-primary/20 text-primary border-primary/30";
        }
    };

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const completedLogs = logs.filter(log => log.status === "completed");

    const scanners = [
        {
            id: "network",
            name: "Network Security Analysis",
            description: "Automated network discovery and vulnerability assessment using Nmap and OpenVAS",
            icon: Network,
            gradient: "from-cyan-500/20 to-blue-500/20",
            iconColor: "text-cyan-400",
            borderColor: "border-cyan-500/30",
        },
        {
            id: "web",
            name: "Web Security Analysis",
            description: "Web application security scanning and traffic stress testing",
            icon: Globe,
            gradient: "from-purple-500/20 to-pink-500/20",
            iconColor: "text-purple-400",
            borderColor: "border-purple-500/30",
        },
        {
            id: "endpoint",
            name: "Endpoint Security Analysis",
            description: "Endpoint hygiene monitoring and threat detection with Wazuh",
            icon: Shield,
            gradient: "from-emerald-500/20 to-teal-500/20",
            iconColor: "text-emerald-400",
            borderColor: "border-emerald-500/30",
        },
    ];

    return (
        <div className="h-screen flex flex-col bg-background overflow-hidden">
            <div className="fixed inset-0 cyber-grid opacity-20 pointer-events-none" />
            <div className="fixed inset-0 bg-gradient-to-b from-accent/5 via-transparent to-transparent pointer-events-none" />

            <CockpitHeader
                onReset={handleReset}
                onSyncIntel={handleSyncIntel}
                systemStatus={systemStatus}
                mode="non-technical"
            />

            <div className="flex-1 flex flex-col overflow-hidden relative z-10 p-4 gap-4">
                {/* TOP SECTION - Horizontal Scanner Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 shrink-0">
                    {scanners.map((scanner, index) => (
                        <motion.div
                            key={scanner.id}
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Card className={`p-4 border-glow hover:border-primary/40 transition-all duration-300 bg-gradient-to-br ${scanner.gradient} ${scanner.borderColor} h-full`}>
                                <div className="flex flex-col h-full">
                                    <div className="flex items-start gap-3 mb-3">
                                        <div className={`h-12 w-12 rounded-lg bg-background/50 flex items-center justify-center shrink-0 ${scanner.borderColor} border`}>
                                            <scanner.icon className={`h-6 w-6 ${scanner.iconColor}`} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-bold text-foreground text-sm mb-1">{scanner.name}</h3>
                                            <p className="text-xs text-muted-foreground line-clamp-2">{scanner.description}</p>
                                        </div>
                                    </div>

                                    <Button
                                        onClick={() => activeScan === scanner.id ? handleStopScan() : handleScanStart(scanner.id as "network" | "web" | "endpoint")}
                                        disabled={activeScan !== null && activeScan !== scanner.id}
                                        className={`w-full mt-auto ${activeScan === scanner.id
                                            ? "bg-red-500/10 hover:bg-red-500/20 border-red-500/50 text-red-500 border"
                                            : `${scanner.iconColor} bg-background/50 hover:bg-background/70 border ${scanner.borderColor}`
                                            }`}
                                        variant="outline"
                                    >
                                        {activeScan === scanner.id ? (
                                            <>
                                                <Square className="h-4 w-4 mr-2 fill-current" />
                                                Stop Scan
                                            </>
                                        ) : (
                                            <>
                                                <Play className="h-4 w-4 mr-2" />
                                                Start Scan
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </Card>
                        </motion.div>
                    ))}
                </div>

                {/* MIDDLE SECTION - Folder Section */}
                <div className="shrink-0">
                    <Card
                        className={`p-4 border-glow bg-card/30 backdrop-blur-sm transition-all duration-300 cursor-pointer hover:border-amber-600/50 hover:bg-amber-900/10 ${completedLogs.length === 0 ? 'opacity-60' : ''
                            }`}
                        onClick={() => {
                            console.log('Folder clicked! Logs count:', completedLogs.length);
                            setShowLogsDialog(true);
                        }}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="h-12 w-12 rounded-lg bg-amber-900/20 border border-amber-700/30 flex items-center justify-center">
                                    {completedLogs.length > 0 ? (
                                        <FolderOpen className="h-7 w-7 text-amber-600" />
                                    ) : (
                                        <Folder className="h-7 w-7 text-amber-700/50" />
                                    )}
                                </div>
                                <div>
                                    <h3 className="font-bold text-foreground text-sm">Generated Scan Logs</h3>
                                    <p className="text-xs text-muted-foreground">
                                        {completedLogs.length === 0
                                            ? "No logs yet - run a scan to generate files"
                                            : `${completedLogs.length} log file${completedLogs.length > 1 ? 's' : ''} ready for analysis`
                                        }
                                    </p>
                                </div>
                            </div>

                            {completedLogs.length > 0 && (
                                <Badge className="bg-amber-900/30 text-amber-600 border-amber-700/30 px-3 py-1">
                                    Click to view files
                                </Badge>
                            )}
                        </div>
                    </Card>
                </div>

                {/* BOTTOM SECTION - Terminal */}
                <div className="flex-1 min-h-0">
                    <TerminalPanel lines={terminalLines} onClear={handleClearTerminal} />
                </div>
            </div>

            {/* User Prompt Dialog for Two-Stage Workflow */}
            <Dialog open={showUserPrompt} onOpenChange={setShowUserPrompt}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-amber-600">
                            <Shield className="h-5 w-5" />
                            Deep Vulnerability Scan
                        </DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4">
                        <p className="text-sm text-foreground">
                            {promptMessage}
                        </p>

                        <div className="bg-amber-900/20 border border-amber-700/30 rounded-lg p-3">
                            <p className="text-xs text-amber-600 font-medium mb-1">⚠ Important Notes:</p>
                            <ul className="text-xs text-muted-foreground space-y-1">
                                <li>• OpenVAS deep scan can take 15-60 minutes</li>
                                <li>• Requires Docker and OpenVAS container running</li>
                                <li>• Provides comprehensive CVE-backed vulnerability assessment</li>
                            </ul>
                        </div>

                        <div className="flex gap-3">
                            <Button
                                onClick={() => handleUserPromptResponse("no")}
                                variant="outline"
                                className="flex-1"
                            >
                                No, Skip OpenVAS
                            </Button>
                            <Button
                                onClick={() => handleUserPromptResponse("yes")}
                                className="flex-1 bg-amber-600 hover:bg-amber-700 text-white"
                            >
                                Yes, Run Deep Scan
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            {/* URL Input Dialog for Web Scan */}
            <Dialog open={showUrlDialog} onOpenChange={setShowUrlDialog}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-purple-400">
                            <Globe className="h-5 w-5" />
                            Web Security Analysis
                        </DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-foreground">Target URL</label>
                            <div className="flex gap-2">
                                <span className="flex items-center px-3 rounded-md border border-input bg-muted/50 text-muted-foreground text-sm">
                                    https://
                                </span>
                                <input
                                    type="text"
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    placeholder="example.com"
                                    value={targetUrl.replace(/^https?:\/\//, '')}
                                    onChange={(e) => setTargetUrl(`https://${e.target.value.replace(/^https?:\/\//, '')}`)}
                                />
                            </div>
                            <p className="text-[10px] text-muted-foreground">
                                Enter the full URL of the web application you want to scan.
                            </p>
                        </div>

                        <div className="bg-purple-900/20 border border-purple-700/30 rounded-lg p-3">
                            <p className="text-xs text-purple-400 font-medium mb-1">⚠ Use Responsibly</p>
                            <p className="text-xs text-muted-foreground">
                                This will launch a real OWASP ZAP attack scan. Only scan targets you own or have permission to test.
                            </p>
                        </div>

                        <div className="flex justify-end gap-2">
                            <Button variant="ghost" onClick={() => setShowUrlDialog(false)}>Cancel</Button>
                            <Button onClick={handleWebScanSubmit} className="bg-purple-600 hover:bg-purple-700 text-white">
                                <Play className="h-3 w-3 mr-2" />
                                Start Analysis
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            {/* Logs Dialog */}
            <Dialog open={showLogsDialog} onOpenChange={setShowLogsDialog}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <FolderOpen className="h-5 w-5 text-amber-600" />
                            Generated Scan Logs
                            <Badge variant="outline" className="ml-auto bg-success/10 text-success border-success/30">
                                {completedLogs.length} Ready
                            </Badge>
                        </DialogTitle>
                    </DialogHeader>

                    <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                        {completedLogs.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-center">
                                <Folder className="h-16 w-16 text-amber-700/20 mb-3" />
                                <p className="text-sm text-muted-foreground">No scan logs yet</p>
                                <p className="text-xs text-muted-foreground/70 mt-1">
                                    Run a security scan to generate logs
                                </p>
                            </div>
                        ) : (
                            completedLogs.map((log, index) => (
                                <motion.div
                                    key={log.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                >
                                    <Card className="p-4 border-glow hover:border-primary/40 transition-all">
                                        <div className="flex items-center gap-3">
                                            <FileText className="h-6 w-6 text-amber-600 shrink-0" />

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <Badge
                                                        variant="outline"
                                                        className={`text-xs ${getScanTypeColor(log.scan_type)}`}
                                                    >
                                                        {log.scan_type}
                                                    </Badge>
                                                </div>
                                                <p className="text-sm font-medium text-foreground truncate">
                                                    {log.file_name}
                                                </p>
                                                <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                                                    <Clock className="h-3 w-3" />
                                                    {formatTimestamp(log.timestamp)}
                                                </div>
                                            </div>

                                            <div className="flex gap-2 shrink-0">
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => handleDownload(log)}
                                                    className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
                                                >
                                                    <Download className="h-4 w-4 mr-2" />
                                                    Download
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => handleDelete(log)}
                                                    className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </Card>
                                </motion.div>
                            ))
                        )}
                    </div>
                </DialogContent>
            </Dialog>

            <footer className="h-8 border-t border-border bg-card/50 px-4 flex items-center justify-between text-[10px] text-muted-foreground">
                <div className="flex items-center gap-4">
                    <span>PredictPath AI v1.0</span>
                    <span className="text-border">|</span>
                    <span>Non-Technical Security Scanner</span>
                </div>
                <div className="flex items-center gap-4">
                    <span>Guided Analysis Mode</span>
                    <span className="text-border">|</span>
                    <span>Backend: Port 8000</span>
                </div>
            </footer>
        </div>
    );
};

export default NonTechnicalMode;
