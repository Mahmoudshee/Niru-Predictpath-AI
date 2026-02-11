
export const TOOLS = [
  {
    id: "Tool1",
    name: "Tool 1: Event Intelligence",
    command: ".\\.venv\\Scripts\\python.exe -m src.main ingest data/samples/lanl_small.txt --type lanl",
    outputFile: "Tool1/data/output/lanl/*.parquet" // Wildcard not directly readable, usually we check success msg or list dir. 
    // Actually, UI just streams terminal. Results panel will check specific files if known.
  },
  {
    id: "Tool2",
    name: "Tool 2: Session Context",
    command: ".\\.venv\\Scripts\\python.exe -m src.main \"..\\Tool1\\data\\output\\**\\*.parquet\"",
    resultFile: "Tool2/risk_assessment.json"
  },
  {
    id: "Tool3",
    name: "Tool 3: Trajectory Engine",
    command: ".\\.venv\\Scripts\\python.exe -m src.main \"..\\Tool2\\risk_assessment.json\"",
    resultFile: "Tool3/trajectory_forecast.json"
  },
  {
    id: "Tool4",
    name: "Tool 4: Adaptive Decision",
    command: ".\\.venv\\Scripts\\python.exe -m src.main \"..\\Tool3\\trajectory_forecast.json\"",
    resultFile: "Tool4/response_plan.json"
  },
  {
    id: "Tool5",
    name: "Tool 5: Controlled Response",
    command: ".\\.venv\\Scripts\\python.exe -m src.main \"..\\Tool4\\response_plan.json\"",
    resultFile: "Tool5/execution_report.json"
  },
  {
    id: "Tool6",
    name: "Tool 6: Governance Learning",
    command: ".\\.venv\\Scripts\\python.exe -m src.main ingest \"..\\Tool5\\execution_report.json\"",
    statusCommand: ".\\.venv\\Scripts\\python.exe -m src.main status",
    resultFile: "Tool6/data/governance.db" // DB file binary, we rely on status output.
  }
];
