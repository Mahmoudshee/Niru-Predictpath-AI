import React, { useState, useEffect, useRef } from 'react';
import { TOOLS } from '../config/tools';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

// Backend URL
const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

export function Cockpit() {
    const [activeTool, setActiveTool] = useState<string | null>(null);
    const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll terminal
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [terminalOutput]);

    const runTool = (toolId: string, cmd: string) => {
        setIsRunning(true);
        setActiveTool(toolId);
        setTerminalOutput(prev => [...prev, `\n--- EXECUTION STARTED: ${toolId} ---\n`]);

        const ws = new WebSocket(`${WS_BASE}/ws/run`);

        ws.onopen = () => {
            ws.send(JSON.stringify({
                tool_dir: toolId,
                command: cmd
            }));
        };

        ws.onmessage = (event) => {
            setTerminalOutput(prev => [...prev, event.data]);
        };

        ws.onclose = () => {
            setIsRunning(false);
            setTerminalOutput(prev => [...prev, `\n--- EXECUTION FINISHED ---\n`]);
        };

        ws.onerror = (err) => {
            setTerminalOutput(prev => [...prev, `\n[ERROR] WebSocket error\n`]);
            setIsRunning(false);
        }
    };

    return (
        <div className="flex h-screen bg-neutral-950 text-neutral-100 font-sans p-4 gap-4">

            {/* LEFT: PIPELINE CONTROL */}
            <Card className="w-1/4 border-neutral-800 bg-neutral-900">
                <CardHeader>
                    <CardTitle className="text-xl font-bold text-cyan-400">PredictPath AI</CardTitle>
                    <p className="text-xs text-neutral-500">Autonomous Defense Pipeline</p>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                    {TOOLS.map((tool) => (
                        <div key={tool.id} className="flex flex-col gap-1">
                            <Button
                                variant={activeTool === tool.id ? "default" : "secondary"}
                                className={`w-full justify-start ${activeTool === tool.id ? "bg-cyan-600 hover:bg-cyan-500" : "bg-neutral-800 hover:bg-neutral-700"}`}
                                onClick={() => runTool(tool.id, tool.command)}
                                disabled={isRunning}
                            >
                                <Badge variant="outline" className="mr-2 border-neutral-600">{tool.id}</Badge>
                                {tool.name}
                            </Button>
                            {/* Extra buttons for Tool 6 status */}
                            {tool.id === "Tool6" && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="ml-8 border-neutral-700 text-xs h-6"
                                    onClick={() => runTool(tool.id, tool.statusCommand!)}
                                    disabled={isRunning}
                                >
                                    Check Status
                                </Button>
                            )}
                        </div>
                    ))}

                    <Separator className="my-4 bg-neutral-800" />

                    <Button variant="destructive" className="w-full" onClick={() => window.location.reload()}>
                        Reset UI
                    </Button>
                </CardContent>
            </Card>

            {/* CENTER: LIVE TERMINAL */}
            <Card className="flex-1 border-neutral-800 bg-black font-mono">
                <CardHeader className="py-3 px-4 border-b border-neutral-800 bg-neutral-900/50">
                    <div className="flex justify-between items-center">
                        <CardTitle className="text-sm font-medium text-neutral-400">Live Terminal Stream</CardTitle>
                        {isRunning && <span className="animate-pulse text-green-500 text-xs">● Running</span>}
                    </div>
                </CardHeader>
                <CardContent className="p-0 h-[calc(100%-3rem)]">
                    <div
                        ref={scrollRef}
                        className="h-full overflow-y-auto p-4 text-xs leading-relaxed text-green-500/90 whitespace-pre-wrap font-mono"
                    >
                        {terminalOutput.map((line, i) => (
                            <span key={i}>{line}</span>
                        ))}
                        <div ref={scrollRef} />
                    </div>
                </CardContent>
            </Card>

            {/* RIGHT: INTELLIGENCE PREVIEW (Placeholder for now) */}
            <Card className="w-1/4 border-neutral-800 bg-neutral-900 border-l">
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-neutral-400">Intelligence Artifacts</CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-neutral-500">
                    <p>Select a tool to verify output artifacts.</p>
                    {/* Future: Fetch and render JSON content */}
                    <div className="mt-4 p-2 bg-neutral-950 rounded border border-neutral-800 h-64 flex items-center justify-center">
                        Preview Inactive
                    </div>
                </CardContent>
            </Card>

        </div>
    );
}
