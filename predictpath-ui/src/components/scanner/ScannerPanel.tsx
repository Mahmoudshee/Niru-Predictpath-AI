import { useState } from "react";
import { motion } from "framer-motion";
import { Network, Globe, Shield, Play, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface ScannerPanelProps {
    onScanStart: (scanType: "network" | "web" | "endpoint") => void;
    activeScan: string | null;
}

export const ScannerPanel = ({ onScanStart, activeScan }: ScannerPanelProps) => {
    const scanners = [
        {
            id: "network" as const,
            title: "Network Security Analysis",
            description: "Automated network discovery and vulnerability assessment using Nmap and OpenVAS",
            icon: Network,
            color: "from-cyan-500/20 to-blue-500/20",
            borderColor: "border-cyan-500/30",
            iconColor: "text-cyan-400",
        },
        {
            id: "web" as const,
            title: "Web Security Analysis",
            description: "Web application security scanning and traffic stress testing",
            icon: Globe,
            color: "from-purple-500/20 to-pink-500/20",
            borderColor: "border-purple-500/30",
            iconColor: "text-purple-400",
        },
        {
            id: "endpoint" as const,
            title: "Endpoint Security Analysis",
            description: "Endpoint hygiene monitoring and threat detection with Wazuh and Velociraptor",
            icon: Shield,
            color: "from-emerald-500/20 to-teal-500/20",
            borderColor: "border-emerald-500/30",
            iconColor: "text-emerald-400",
        },
    ];

    return (
        <div className="h-full flex flex-col p-4 bg-card/30 backdrop-blur-sm border-r border-border">
            <div className="mb-4">
                <h2 className="text-lg font-bold text-foreground mb-1">Security Scanners</h2>
                <p className="text-xs text-muted-foreground">
                    Select a guided security analysis to run
                </p>
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto custom-scrollbar">
                {scanners.map((scanner, index) => {
                    const Icon = scanner.icon;
                    const isActive = activeScan === scanner.id;

                    return (
                        <motion.div
                            key={scanner.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Card
                                className={`
                  scanner-card p-4 border-2 transition-all duration-300
                  bg-gradient-to-br ${scanner.color}
                  ${scanner.borderColor}
                  ${isActive ? "ring-2 ring-primary/50 scale-[1.02]" : "hover:scale-[1.01]"}
                  backdrop-blur-sm
                `}
                            >
                                <div className="flex items-start gap-3">
                                    <div className={`
                    h-12 w-12 rounded-lg flex items-center justify-center
                    bg-background/50 border ${scanner.borderColor}
                  `}>
                                        <Icon className={`h-6 w-6 ${scanner.iconColor}`} />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-semibold text-sm text-foreground mb-1">
                                            {scanner.title}
                                        </h3>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            {scanner.description}
                                        </p>
                                    </div>
                                </div>

                                <Button
                                    onClick={() => onScanStart(scanner.id)}
                                    disabled={activeScan !== null}
                                    className={`
                    w-full mt-3 h-9
                    ${isActive
                                            ? "bg-primary/20 text-primary border-primary/30"
                                            : "bg-background/50 hover:bg-background/70"
                                        }
                  `}
                                    variant={isActive ? "default" : "outline"}
                                >
                                    {isActive ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Scanning...
                                        </>
                                    ) : (
                                        <>
                                            <Play className="h-4 w-4 mr-2" />
                                            Start Scan
                                        </>
                                    )}
                                </Button>
                            </Card>
                        </motion.div>
                    );
                })}
            </div>

            <div className="mt-4 p-3 rounded-lg bg-primary/5 border border-primary/20">
                <p className="text-xs text-muted-foreground">
                    <span className="text-primary font-medium">💡 Tip:</span> Generated logs are automatically
                    compatible with PredictPath AI's 6-tool pipeline
                </p>
            </div>
        </div>
    );
};
