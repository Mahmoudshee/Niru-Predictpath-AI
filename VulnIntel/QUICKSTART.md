# VulnIntel Quick Start Guide

## Installation

### 1. Create Virtual Environment

```powershell
cd VulnIntel
python -m venv .venv
```

### 2. Activate Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Package

```powershell
pip install -e .
```

## First-Time Setup

### Initialize Database

```powershell
python -m src.main init
```

Expected output:
```
Database initialized: C:\...\VulnIntel\data\db\vuln.db
✅ Database initialized successfully
```

### Initial Data Sync

```powershell
python -m src.main sync --all
```

This will:
- Download recent CVEs (last 8 days) from NVD
- Download complete CWE catalog from MITRE
- Download KEV catalog from CISA

Expected time: 3-5 minutes

## Basic Usage

### Check Sync Status

```powershell
python -m src.main status
```

### View Statistics

```powershell
python -m src.main stats
```

### Query a CVE

```powershell
python -m src.main query cve CVE-2024-1234
```

### Check if CVE is Exploited

```powershell
python -m src.main query is-exploited CVE-2024-1234
```

### Get High-Risk CVEs

```powershell
python -m src.main query high-risk --min-cvss 9.0
```

### Get Only Exploited CVEs

```powershell
python -m src.main query high-risk --kev-only
```

### Get Recent KEV Additions

```powershell
python -m src.main query kev --days 30
```

## Programmatic Usage

```python
from src.query.api import VulnIntelAPI

# Initialize API
api = VulnIntelAPI()

# Get CVE details
cve = api.get_cve_by_id("CVE-2024-1234")
if cve:
    print(f"CVSS: {cve['cvss_v3_score']}")
    print(f"Severity: {cve['cvss_v3_severity']}")
    print(f"Description: {cve['description']}")

# Check exploit status
if api.is_cve_exploited("CVE-2024-1234"):
    print("⚠️ This CVE is actively exploited!")

# Get high-risk CVEs
high_risk = api.get_high_risk_cves(min_cvss=9.0, kev_only=True)
for cve in high_risk:
    print(f"{cve['cve_id']}: {cve['cvss_v3_score']}")

# Get statistics
stats = api.get_vuln_stats()
print(f"Total CVEs: {stats['cve']:,}")
print(f"Total KEV entries: {stats['kev']:,}")
```

## Maintenance

### Update Data

```powershell
# Update all sources
python -m src.main sync --all

# Update specific source
python -m src.main sync --cve
python -m src.main sync --kev
```

### Force Update (Ignore Schedule)

```powershell
python -m src.main sync --all --force
```

### Vacuum Database (Reclaim Space)

```powershell
python -m src.main vacuum
```

## Troubleshooting

### Database Not Found

If you see "Database not found", run:
```powershell
python -m src.main init
```

### Sync Failures

Check logs:
```powershell
type data\logs\vulnintel.log
```

### Reset Database

```powershell
python -m src.main init --force
python -m src.main sync --all
```

## Integration with PredictPath AI Tools

### Tool 1 (Event Intelligence)

```python
from src.query.api import VulnIntelAPI

api = VulnIntelAPI()

# Enrich event with CVE data
if "CVE-" in event_description:
    cve_id = extract_cve_id(event_description)
    cve_data = api.get_cve_by_id(cve_id)
    
    if cve_data:
        event['cvss_score'] = cve_data['cvss_v3_score']
        event['is_exploited'] = api.is_cve_exploited(cve_id)
        event['cwe_ids'] = cve_data['cwe_ids']
```

### Tool 2 (Session Context)

```python
# Amplify risk for exploited vulnerabilities
if api.is_cve_exploited(session_cve):
    risk_multiplier = 2.0
    risk_score *= risk_multiplier
```

### Tool 3 (Predictive Trajectory)

```python
# Get related CVEs via CWE
related_cves = api.get_cves_by_cwe("CWE-79", limit=50)
exploited_cves = [cve for cve in related_cves if api.is_cve_exploited(cve['cve_id'])]

# Prioritize paths with exploited CVEs
for cve in exploited_cves:
    trajectory_weight += 1.5
```

### Tool 4 (Adaptive Decision)

```python
# Recommend patches for KEV CVEs
kev_entries = api.get_kev_entries(days_back=7)

for entry in kev_entries:
    actions.append({
        "type": "patch",
        "cve": entry['cve_id'],
        "urgency": "critical",
        "due_date": entry['due_date'],
        "ransomware_risk": entry['known_ransomware_use'] == "Known"
    })
```

## Next Steps

1. ✅ Initialize database
2. ✅ Sync all data sources
3. ✅ Test queries
4. ✅ Integrate with Tools 1-6
5. ✅ Set up automated sync (Task Scheduler)

For more details, see `README.md` and `IMPLEMENTATION_PLAN.md`.
