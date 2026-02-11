import { motion } from "framer-motion";
import { Shield, Activity, Bell, Settings, User } from "lucide-react";

export function Header() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl"
    >
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-4 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 animate-pulse-ring rounded-lg bg-primary/20" />
            <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-foreground">
              PredictPath<span className="text-primary"> AI</span>
            </h1>
            <p className="text-[10px] font-medium tracking-wider text-muted-foreground uppercase">
              Predictive Cyber Defense
            </p>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-6">
          <nav className="flex items-center gap-1">
            {[
              { label: "Dashboard", active: true },
              { label: "Attack Graph", active: false },
              { label: "Threats", active: false },
              { label: "Analytics", active: false },
            ].map((item) => (
              <button
                key={item.label}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  item.active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-2 rounded-lg bg-success/10 px-3 py-1.5">
            <Activity className="h-4 w-4 text-success" />
            <span className="text-xs font-medium text-success">
              System Healthy
            </span>
          </div>

          <button className="relative rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
            <Bell className="h-5 w-5" />
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-critical animate-pulse" />
          </button>

          <button className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
            <Settings className="h-5 w-5" />
          </button>

          <button className="flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 transition-colors hover:bg-secondary/80">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
              MS
            </div>
            <span className="hidden lg:inline text-sm font-medium text-foreground">
              Mahmoud
            </span>
          </button>
        </div>
      </div>
    </motion.header>
  );
}
