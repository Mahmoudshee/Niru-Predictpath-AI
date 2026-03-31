import React, { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, Download, Loader2, FolderClosed, Trash2 } from "lucide-react";

interface AuditFile {
    filename: string;
    path: string;
    size_bytes: number;
    generated_at: string;
}

interface AuditFolderDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

const API_BASE = "";

export function AuditFolderDialog({ open, onOpenChange }: AuditFolderDialogProps) {
    const [audits, setAudits] = useState<AuditFile[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchAudits = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/tool6/audits`);
            if (!res.ok) throw new Error("Failed to fetch audit records.");
            const data = await res.json();
            if (data.available && data.audits) {
                setAudits(data.audits);
            } else {
                setAudits([]);
                if (data.message && data.message.includes("error")) {
                    setError(data.message);
                }
            }
        } catch (err: any) {
            setError(err.message || "An error occurred while fetching audit logs.");
            setAudits([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (open) {
            fetchAudits();
        }
    }, [open]);

    const formatSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const handleDownload = (path: string) => {
        window.open(`${API_BASE}/api/download?path=${encodeURIComponent(path)}`, "_blank");
    };

    const handleDelete = async (path: string) => {
        if (!confirm("Are you sure you want to delete this audit report?")) return;
        
        try {
            const res = await fetch(`${API_BASE}/api/file?path=${encodeURIComponent(path)}`, {
                method: "DELETE"
            });
            
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to delete file");
            }
            
            // Refresh list
            fetchAudits();
        } catch (err: any) {
            alert(err.message || "Failed to delete file");
        }
    };

    const handleClearAll = async () => {
        if (!confirm("Are you sure you want to delete ALL audit reports? This cannot be undone.")) return;
        setLoading(true);
        try {
            await Promise.all(audits.map(audit => 
                fetch(`${API_BASE}/api/file?path=${encodeURIComponent(audit.path)}`, {
                    method: "DELETE"
                })
            ));
            fetchAudits();
        } catch (err: any) {
            alert("An error occurred while deleting some files.");
            fetchAudits();
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[700px] border-border bg-background">
                <DialogHeader>
                    <div className="flex items-center justify-between pr-8">
                        <DialogTitle className="flex items-center gap-2 text-foreground">
                            <FolderClosed className="h-5 w-5 text-primary" />
                            Generated Audit Reports Folder
                        </DialogTitle>
                        {audits.length > 0 && !loading && (
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={handleClearAll}
                                className="h-8 shadow-sm flex items-center gap-2"
                            >
                                <Trash2 className="h-4 w-4" />
                                <span>Clear All</span>
                            </Button>
                        )}
                    </div>
                    <DialogDescription>
                        Access historically auto-generated Governance Audit PDFs from full pipeline executions.
                    </DialogDescription>
                </DialogHeader>

                <div className="mt-4">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                            <Loader2 className="h-8 w-8 animate-spin mb-4" />
                            <p>Loading audit reports...</p>
                        </div>
                    ) : error ? (
                        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive">
                            <p>{error}</p>
                            <Button variant="outline" size="sm" onClick={fetchAudits} className="mt-2">
                                Retry
                            </Button>
                        </div>
                    ) : audits.length === 0 ? (
                        <div className="flex flex-col items-center justify-center p-12 text-muted-foreground bg-card/30 rounded-lg border border-border border-dashed">
                            <FileText className="h-12 w-12 mb-4 opacity-50" />
                            <p className="text-lg font-medium text-foreground">Folder is Empty</p>
                            <p className="text-sm">No audit reports have been generated yet.</p>
                        </div>
                    ) : (
                        <ScrollArea className="h-[400px] rounded-md border border-border">
                            <div className="flex flex-col gap-2 p-3">
                                {audits.map((audit) => (
                                    <div 
                                        key={audit.path}
                                        className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-card/50 hover:bg-card hover:border-border transition-colors group"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center shrink-0">
                                                <FileText className="h-5 w-5 text-primary" />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-foreground line-clamp-1">{audit.filename}</span>
                                                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                                    <span>{formatSize(audit.size_bytes)}</span>
                                                    <span className="text-border">•</span>
                                                    <span>{new Date(audit.generated_at).toLocaleString()}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="border-primary/20 hover:bg-primary/10 text-primary h-8"
                                                onClick={() => handleDownload(audit.path)}
                                            >
                                                <Download className="h-3.5 w-3.5 mr-1.5" />
                                                <span className="text-xs">Download</span>
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="border-destructive/20 hover:bg-destructive/10 text-destructive h-8 px-2"
                                                onClick={() => handleDelete(audit.path)}
                                                title="Delete Report"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
