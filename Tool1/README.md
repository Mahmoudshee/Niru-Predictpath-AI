# PredictPath AI - Tool 1: Data Ingestion & Sanitization

## 📋 Overview
Tool 1 is the entry point for the PredictPath AI pipeline. It handles the ingestion of raw security logs from various sources (SIEM, Firewall, IDs), cleanses the data, and prepares it for analysis.

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.8+
- Git

### 2. Setup Virtual Environment
Run the setup script or manually create the environment:

**Windows:**
```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Missing Files (Git Ignored)
The following directories are **not** included in the repo (for size reasons) and will be auto-generated when you run the tool:
- `data/` - Stores raw and processed logs
- `logs/` - Application logs
- `models/` - Local AI models (downloaded on first run)

### 4. Running the Tool
```bash
python main.py
```

## 🛠️ Configuration
Edit `config.yaml` to adjust:
- Ingestion batch size
- Source directory paths
- Log retention policies

## 📄 Output
Processed logs are saved to `data/output/` in JSON format, ready for Tool 2.
