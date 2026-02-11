# PredictPath AI - Operation Cockpit

This is the React-based Operator UI for the PredictPath System.

## 🚀 Quick Start

1. **Install Frontend Dependencies**:
```powershell
npm install
```

2. **Setup Backend**:
```powershell
python -m venv venv_backend
.\venv_backend\Scripts\pip install -r backend/requirements.txt
```

3. **Run All (Parallel)**:
You need two terminals.

Terminal 1 (Backend):
```powershell
.\venv_backend\Scripts\python.exe backend/main.py
```

Terminal 2 (Frontend):
```powershell
npm run dev
```

Open `http://localhost:5173` in your browser.

## ⚙️ Architecture

- **Frontend**: React + Vite + Tailwind (Shadcn UI)
- **Backend**: FastAPI + WebSockets (Bridges UI to Shell)
- **Orchestration**: Executes Python CLIs (`Tool1`...`Tool6`) via subprocess.

The UI streams `stdout/stderr` in real time, providing a SOC-like console experience.
