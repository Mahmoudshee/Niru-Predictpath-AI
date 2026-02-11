import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Terminal, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export const ModeToggle = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const isNonTechnical = location.pathname === "/non-technical";

    return (
        <div className="flex items-center gap-1 bg-card/50 rounded-lg p-1 border border-border/50">
            <Button
                variant={isNonTechnical ? "default" : "ghost"}
                size="sm"
                onClick={() => navigate("/non-technical")}
                className={`relative h-8 px-3 ${isNonTechnical
                        ? "bg-primary/20 text-primary hover:bg-primary/30 border-primary/30"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
            >
                {isNonTechnical && (
                    <motion.div
                        layoutId="mode-indicator"
                        className="absolute inset-0 bg-primary/10 rounded-md border border-primary/30"
                        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                )}
                <Wand2 className="h-3.5 w-3.5 mr-1.5 relative z-10" />
                <span className="text-xs font-medium relative z-10">Non-Technical</span>
            </Button>

            <Button
                variant={!isNonTechnical ? "default" : "ghost"}
                size="sm"
                onClick={() => navigate("/")}
                className={`relative h-8 px-3 ${!isNonTechnical
                        ? "bg-primary/20 text-primary hover:bg-primary/30 border-primary/30"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
            >
                {!isNonTechnical && (
                    <motion.div
                        layoutId="mode-indicator"
                        className="absolute inset-0 bg-primary/10 rounded-md border border-primary/30"
                        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                )}
                <Terminal className="h-3.5 w-3.5 mr-1.5 relative z-10" />
                <span className="text-xs font-medium relative z-10">Technical</span>
            </Button>
        </div>
    );
};
