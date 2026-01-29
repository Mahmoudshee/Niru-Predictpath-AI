# PredictPath AI - Tool 3: Trajectory Forecasting

## 📋 Overview
Tool 3 forecasts the future trajectory of detected threats. It uses time-series analysis to estimate the time-to-impact for identified risks.

## 🚀 Quick Start

### 1. Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

### 2. Running
```bash
python main.py
```

### 3. Data Flow
- Inputs: Attack paths from Tool 2
- Outputs: Forecast JSONs in `results/`
