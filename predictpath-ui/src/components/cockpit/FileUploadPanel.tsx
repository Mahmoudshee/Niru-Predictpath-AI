import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: "pending" | "ready" | "error";
  serverPath?: string;
}

interface FileUploadPanelProps {
  onFilesReady: (files: UploadedFile[]) => void;
  onClear: () => void;
}

const API_BASE = "http://localhost:8000";

export const FileUploadPanel = ({ onFilesReady, onClear }: FileUploadPanelProps) => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    processFiles(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      processFiles(selectedFiles);
    }
  }, []);

  const processFiles = async (newFiles: File[]) => {
    // 1. Create Placeholder Entries
    const newEntries: UploadedFile[] = newFiles.map(file => ({
      id: `file-${Date.now()}-${file.name}`,
      name: file.name,
      size: file.size,
      status: "pending"
    }));

    setFiles(prev => [...prev, ...newEntries]);

    // 2. Upload Each File
    const updatedEntries = [...newEntries];

    for (let i = 0; i < newFiles.length; i++) {
      const file = newFiles[i];
      const entry = updatedEntries[i];

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch(`${API_BASE}/api/upload`, {
          method: "POST",
          body: formData
        });

        if (!res.ok) throw new Error("Upload Failed");

        const data = await res.json();
        entry.status = "ready";
        entry.serverPath = data.path; // e.g. "data/uploads/filename"

      } catch (err) {
        entry.status = "error";
        console.error(err);
      }
    }

    // 3. Update State & Notify Parent
    setFiles(prev => {
      // Merge pending updates
      const final = prev.map(p => {
        const updated = updatedEntries.find(u => u.id === p.id);
        return updated || p;
      });

      // Only notify parent of READY files
      const readyFiles = final.filter(f => f.status === "ready");
      onFilesReady(readyFiles);

      return final;
    });
  };

  const removeFile = (id: string) => {
    setFiles((prev) => {
      const updated = prev.filter((f) => f.id !== id);
      onFilesReady(updated.filter(f => f.status === "ready"));
      return updated;
    });
  };

  const handleClearAll = () => {
    setFiles([]);
    onClear();
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-3 border-b border-border bg-card/50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Upload className="h-3.5 w-3.5 text-primary" />
          <span className="text-xs font-medium">Log Files</span>
        </div>
        {files.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearAll}
            className="h-5 px-2 text-[10px] text-muted-foreground hover:text-destructive"
          >
            Clear
          </Button>
        )}
      </div>

      {/* Compact Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border border-dashed rounded-md p-2 text-center transition-all cursor-pointer
          ${isDragging
            ? "border-primary bg-primary/10"
            : "border-border hover:border-primary/50 hover:bg-card/80"
          }
        `}
      >
        <input
          type="file"
          multiple
          accept=".log,.txt,.json,.csv,.evtx,.xml"
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <div className="flex items-center justify-center gap-2">
          {!isDragging && <Upload className="h-3.5 w-3.5 text-muted-foreground" />}
          <div className="text-[11px] text-muted-foreground">
            {isDragging ? "Drop to upload" : <span>Drop or <span className="text-primary hover:underline">browse</span></span>}
          </div>
        </div>
      </div>

      {/* Condensed File List */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 space-y-1 max-h-[120px] overflow-y-auto pr-1 custom-scrollbar bg-black/20 rounded-md"
          >
            {files.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -5 }}
                className="flex items-center gap-2 p-1.5 rounded border border-white/5 hover:bg-white/5 group"
              >
                <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
                  <span className="text-[10px] font-medium truncate max-w-[120px]" title={file.name}>{file.name}</span>
                  <span className="text-[9px] text-muted-foreground shrink-0">{formatSize(file.size)}</span>
                </div>

                {file.status === "pending" && <Loader2 className="h-3 w-3 text-primary animate-spin shrink-0" />}
                {file.status === "ready" && <CheckCircle className="h-3 w-3 text-success shrink-0" />}
                {file.status === "error" && <AlertCircle className="h-3 w-3 text-destructive shrink-0" />}

                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => removeFile(file.id)}
                >
                  <X className="h-2.5 w-2.5" />
                </Button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export type { UploadedFile };
