import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FolderOpen, Folder, Download, ArrowRight, FileText, Clock, Sparkles, ChevronDown, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface ScanLog {
    id: string;
    scan_type: string;
    timestamp: string;
    status: "completed" | "failed";
    log_path: string;
    file_name: string;
}

interface LogStoragePanelProps {
    refreshTrigger?: number;
}

const API_BASE = "http://localhost:8000";

export const LogStoragePanel = ({ refreshTrigger }: LogStoragePanelProps) => {
    const [logs, setLogs] = useState<ScanLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [isExpanded, setIsExpanded] = useState(false);
    const navigate = useNavigate();

    const fetchLogs = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/scans/history`);
            if (res.ok) {
                const data = await res.json();
                setLogs(data.scans || []);
            }
        } catch (error) {
            console.error("Failed to fetch scan history:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, [refreshTrigger]);

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

    const completedLogs = logs.filter(log => log.status === "completed");

    return (
        <div className="h-full flex flex-col p-4 bg-card/30 backdrop-blur-sm">
            <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                    <h2 className="text-lg font-bold text-foreground">Generated Logs</h2>
                    <Badge variant="outline" className="bg-success/10 text-success border-success/30">
                        <Sparkles className="h-3 w-3 mr-1" />
                        {completedLogs.length} Ready
                    </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                    Click folder to view and download scan logs
                </p>
            </div>

            {/* Folder View */}
            <div className="flex-1 flex flex-col items-center justify-center">
                {loading ? (
                    <div className="text-muted-foreground text-sm">Loading...</div>
                ) : logs.length === 0 ? (
                    <div className="flex flex-col items-center text-center">
                        <Folder className="h-24 w-24 text-muted-foreground/20 mb-4" />
                        <p className="text-sm text-muted-foreground font-medium">No scans yet</p>
                        <p className="text-xs text-muted-foreground/70 mt-1">
                            Run a security scan to generate logs
                        </p>
                    </div>
                ) : (
                    <div className="w-full">
                        {/* Folder Icon Button */}
                        <motion.div
                            className="flex flex-col items-center mb-4 cursor-pointer"
                            onClick={() => setIsExpanded(!isExpanded)}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            {isExpanded ? (
                                <FolderOpen className="h-20 w-20 text-primary mb-2" />
                            ) : (
                                <Folder className="h-20 w-20 text-primary mb-2" />
                            )}
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-foreground">
                                    Scan Logs ({completedLogs.length})
                                </span>
                                {isExpanded ? (
                                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                ) : (
                                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                                {isExpanded ? "Click to collapse" : "Click to expand"}
                            </p>
                        </motion.div>

                        {/* Expandable File List */}
                        <AnimatePresence>
                            {isExpanded && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="overflow-hidden"
                                >
                                    <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
                                        {completedLogs.map((log, index) => (
                                            <motion.div
                                                key={log.id}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: index * 0.05 }}
                                            >
                                                <Card className="p-3 border-glow hover:border-primary/40 transition-all duration-300">
                                                    <div className="flex items-center gap-3">
                                                        <FileText className="h-5 w-5 text-primary shrink-0" />

                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <Badge
                                                                    variant="outline"
                                                                    className={`text-xs ${getScanTypeColor(log.scan_type)}`}
                                                                >
                                                                    {log.scan_type}
                                                                </Badge>
                                                            </div>
                                                            <p className="text-xs font-medium text-foreground truncate">
                                                                {log.file_name}
                                                            </p>
                                                            <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                                                                <Clock className="h-3 w-3" />
                                                                {formatTimestamp(log.timestamp)}
                                                            </div>
                                                        </div>

                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={() => handleDownload(log)}
                                                            className="h-8 px-2 shrink-0"
                                                        >
                                                            <Download className="h-3.5 w-3.5" />
                                                        </Button>
                                                    </div>
                                                </Card>
                                            </motion.div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}
            </div>

            {/* Action Buttons */}
            {completedLogs.length > 0 && (
                <div className="mt-4 space-y-2">
                    <Button
                        onClick={() => navigate("/")}
                        className="w-full bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30"
                        variant="outline"
                    >
                        <ArrowRight className="h-4 w-4 mr-2" />
                        Switch to Technical Mode
                    </Button>

                    <div className="p-3 rounded-lg bg-accent/5 border border-accent/20">
                        <p className="text-xs text-muted-foreground">
                            <span className="text-accent font-medium">💡 Next Step:</span> Upload logs to Tool 1 for AI analysis
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};
