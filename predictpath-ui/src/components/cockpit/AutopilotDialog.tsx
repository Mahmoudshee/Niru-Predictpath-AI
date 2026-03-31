import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Bot, Clock, Zap } from "lucide-react";

interface AutopilotDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStart: (durationSeconds: number) => void;
}

/** Parse natural language duration strings like "2 hrs", "30min", "1 day 4 hours", "2 weeks" etc. */
export function parseDuration(input: string): number | null {
  const normalized = input.toLowerCase().trim();
  let totalSeconds = 0;
  let matched = false;

  const patterns: [RegExp, number][] = [
    [/(\d+(?:\.\d+)?)\s*(?:month|months|mo)/g, 30 * 24 * 3600],
    [/(\d+(?:\.\d+)?)\s*(?:week|weeks|wk|wks)/g, 7 * 24 * 3600],
    [/(\d+(?:\.\d+)?)\s*(?:day|days|d)/g, 24 * 3600],
    [/(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|h)/g, 3600],
    [/(\d+(?:\.\d+)?)\s*(?:minute|minutes|min|mins|m)/g, 60],
    [/(\d+(?:\.\d+)?)\s*(?:second|seconds|sec|secs|s)/g, 1],
  ];

  for (const [pattern, multiplier] of patterns) {
    let m;
    pattern.lastIndex = 0;
    while ((m = pattern.exec(normalized)) !== null) {
      totalSeconds += parseFloat(m[1]) * multiplier;
      matched = true;
    }
  }

  // If no keywords found, try plain bare number → treat as hours
  if (!matched) {
    const bare = parseFloat(normalized);
    if (!isNaN(bare) && bare > 0) {
      totalSeconds = bare * 3600;
      matched = true;
    }
  }

  return matched && totalSeconds > 0 ? Math.round(totalSeconds) : null;
}

export function formatCountdown(seconds: number): string {
  if (seconds <= 0) return "00:00:00";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  if (d > 0) return `${d}d ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

const EXAMPLES = [
  "2 hrs",
  "30 min",
  "1 day",
  "4 hours 30 minutes",
  "1 week",
  "2 months",
];

export const AutopilotDialog = ({ open, onOpenChange, onStart }: AutopilotDialogProps) => {
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<string | null>(null);

  const handleInputChange = (value: string) => {
    setInput(value);
    setError("");
    const secs = parseDuration(value);
    if (secs !== null) {
      setPreview(formatCountdown(secs));
    } else {
      setPreview(null);
    }
  };

  const handleStart = () => {
    const secs = parseDuration(input);
    if (!secs) {
      setError("Couldn't understand that duration. Try: '2 hrs', '30 min', '1 day 4 hours'");
      return;
    }
    onStart(secs);
    setInput("");
    setError("");
    setPreview(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md border-primary/30 bg-card/95 backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-primary">
            <div className="h-8 w-8 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center">
              <Bot className="h-4 w-4" />
            </div>
            Autopilot Mode
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-xs text-muted-foreground space-y-1">
            <p className="text-primary font-medium flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5" /> What Autopilot Does:
            </p>
            <ul className="space-y-0.5 pl-4">
              <li>• Runs <strong className="text-foreground">Endpoint Security</strong> scan first</li>
              <li>• Then runs <strong className="text-foreground">Network (Nmap only)</strong> scan</li>
              <li>• Repeats the cycle continuously</li>
              <li>• Saves all logs with timestamps automatically</li>
              <li>• Stops when the countdown timer ends</li>
            </ul>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-primary" />
              How long should Autopilot run?
            </label>
            <Input
              placeholder="e.g. 2 hrs, 30 min, 1 day 4 hours, 2 weeks"
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleStart()}
              className="bg-background/50 border-primary/30 focus:border-primary"
              autoFocus
            />
            {error && (
              <p className="text-xs text-destructive">{error}</p>
            )}
            {preview && (
              <p className="text-xs text-success flex items-center gap-1.5">
                ✅ Countdown will run for: <span className="font-mono font-bold">{preview}</span>
              </p>
            )}
          </div>

          <div className="space-y-1">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Quick examples:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => handleInputChange(ex)}
                  className="text-xs px-2 py-1 rounded bg-secondary hover:bg-secondary/80 text-secondary-foreground border border-border transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter className="flex gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            onClick={handleStart}
            className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
            disabled={!preview}
          >
            <Bot className="h-4 w-4" />
            Start Autopilot
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
