import { motion } from "framer-motion";
import { Shield, Activity, Clock, Settings, HelpCircle, LogOut } from "lucide-react";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ResetControls, ResetLevel } from "./ResetControls";
import { ModeToggle } from "@/components/navigation/ModeToggle";

interface CockpitHeaderProps {
  onReset: (level: ResetLevel) => void;
  onSyncIntel: () => void;
  systemStatus: "idle" | "running" | "error";
  mode?: "technical" | "non-technical";
}

export const CockpitHeader = ({ onReset, onSyncIntel, systemStatus, mode = "technical" }: CockpitHeaderProps) => {
  const getStatusBadge = () => {
    switch (systemStatus) {
      case "running":
        return (
          <Badge className="bg-primary/20 text-primary border-primary/30">
            <Activity className="h-3 w-3 mr-1 animate-pulse" />
            Pipeline Running
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive">
            <span className="h-2 w-2 rounded-full bg-destructive mr-1.5" />
            Error
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-muted-foreground mr-1.5" />
            Idle
          </Badge>
        );
    }
  };

  return (
    <header className="h-14 border-b border-border bg-card/80 backdrop-blur-sm px-4 flex items-center justify-between">
      {/* Left - Branding */}
      <div className="flex items-center gap-3">
        <motion.div
          className="flex items-center gap-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-foreground leading-tight">
              PredictPath AI
            </span>
            <span className="text-[10px] text-muted-foreground leading-tight">
              Command Cockpit
            </span>
          </div>
        </motion.div>

        <div className="h-6 w-px bg-border mx-2" />

        {getStatusBadge()}
      </div>

      {/* Center - Connection Status */}
      <div className="hidden md:flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
          <span>PowerShell Connected</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          <span>Tool Folders Mounted</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          <span className="font-mono">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Right - Controls */}
      <div className="flex items-center gap-2">
        <ModeToggle />

        <div className="h-6 w-px bg-border mx-1" />

        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-2 border-primary/30 hover:bg-primary/10 text-primary"
          onClick={onSyncIntel}
        >
          <Activity className="h-4 w-4" />
          <span>Sync Intel</span>
        </Button>

        <div className="h-6 w-px bg-border mx-1" />

        <ResetControls onReset={onReset} mode={mode} />

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Settings className="h-4 w-4" />
        </Button>

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <HelpCircle className="h-4 w-4" />
        </Button>

        <div className="h-6 w-px bg-border mx-1" />

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive transition-colors"
          onClick={() => signOut(auth)}
          title="Sign Out"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
};
