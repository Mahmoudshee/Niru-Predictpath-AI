import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Trash2, Download, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TerminalLine {
  id: string;
  type: "command" | "stdout" | "stderr" | "info" | "success" | "warning" | "error";
  content: string;
  timestamp: Date;
}

interface TerminalPanelProps {
  lines: TerminalLine[];
  onClear: () => void;
}

export const TerminalPanel = ({ lines, onClear }: TerminalPanelProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  const getLineColor = (type: TerminalLine["type"]) => {
    switch (type) {
      case "command":
        return "text-primary";
      case "stdout":
        return "text-foreground";
      case "stderr":
        return "text-destructive";
      case "info":
        return "text-muted-foreground";
      case "success":
        return "text-success";
      case "warning":
        return "text-warning";
      case "error":
        return "text-destructive";
      default:
        return "text-foreground";
    }
  };

  const getLinePrefix = (type: TerminalLine["type"]) => {
    switch (type) {
      case "command":
        return ">";
      case "stderr":
        return "!";
      case "info":
        return "#";
      case "success":
        return "✓";
      case "warning":
        return "⚠";
      case "error":
        return "✖";
      default:
        return " ";
    }
  };

  const handleCopyAll = () => {
    const text = lines.map((l) => `${getLinePrefix(l.type)} ${l.content}`).join("\n");
    navigator.clipboard.writeText(text);
  };

  const handleExport = () => {
    const text = lines
      .map((l) => `[${l.timestamp.toISOString()}] [${l.type.toUpperCase()}] ${l.content}`)
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `predictpath-terminal-${Date.now()}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-black/50 rounded-lg border border-border overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card/50">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-foreground">Live Terminal</span>
          <span className="text-xs text-muted-foreground">
            {lines.length} lines
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleCopyAll}
            title="Copy all"
          >
            <Copy className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleExport}
            title="Export log"
          >
            <Download className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onClear}
            title="Clear terminal"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Terminal Content */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-2.5 font-mono text-xs leading-relaxed"
      >
        {lines.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <Terminal className="h-12 w-12 mb-4 opacity-20" />
            <p className="text-sm">Terminal ready</p>
            <p className="text-xs mt-1">Execute a tool to see live output</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {lines.map((line, index) => (
              <motion.div
                key={line.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.1 }}
                className={`flex gap-2 ${getLineColor(line.type)}`}
              >
                <span className="opacity-50 select-none w-4 text-right shrink-0">
                  {getLinePrefix(line.type)}
                </span>
                <span className="opacity-30 text-[10px] shrink-0">
                  {line.timestamp.toLocaleTimeString()}
                </span>
                <span className="break-all">{line.content}</span>
              </motion.div>
            ))}
            {/* Blinking cursor */}
            <div className="flex gap-2 items-center">
              <span className="opacity-50 select-none w-4 text-right shrink-0">
                &gt;
              </span>
              <span className="w-2 h-4 bg-primary animate-pulse" />
            </div>
          </div>
        )}
      </div>

      {/* Footer Status */}
      <div className="px-4 py-2 border-t border-border bg-card/30 text-[10px] text-muted-foreground flex items-center justify-between">
        <span>PowerShell • Real CLI Execution Mode</span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
          Connected
        </span>
      </div>
    </div>
  );
};

export type { TerminalLine };
