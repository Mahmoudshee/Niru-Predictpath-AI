# 🛡️ VulnIntel — Vulnerability Intelligence Data Pipeline

## Overview

**VulnIntel** is a standalone, production-ready vulnerability intelligence subsystem for **PredictPath AI**. It automatically ingests, normalizes, and stores vulnerability data from authoritative sources (NVD, MITRE, CISA) and provides clean query interfaces for security analytics.

---

## Features

✅ **Authoritative Data Sources**
- CVE data from NVD (JSON 2.0 feeds)
- CWE classifications from MITRE
- KEV (Known Exploited Vulnerabilities) from CISA

✅ **Local-First Architecture**
- SQLite database (no cloud dependency)
- Offline-capable after initial sync
- Deterministic, demo-safe behavior

✅ **Automated Updates**
- Incremental CVE updates (every 2-6 hours)
- Daily KEV refresh
- Weekly CWE updates

✅ **Clean Query Interface**
- Python API for programmatic access
- JSON-serializable outputs
- Optimized for read-heavy analytics

---

## Quick Start

### 1. Installation

```powershell
cd VulnIntel
python -m venv .venv
.\.venv\Scripts\pip install -e .
```

### 2. Initialize Database

```powershell
.\.venv\Scripts\python -m src.main init
```

### 3. Initial Sync (All Sources)

```powershell
.\.venv\Scripts\python -m src.main sync --all
```

This will download and process:
- Recent CVEs (last 8 days)
- Complete CWE catalog
- Current KEV list

**Expected time:** 3-5 minutes

---

## Usage

### Sync Operations

```powershell
# Sync all sources
python -m src.main sync --all

# Sync specific source
python -m src.main sync --cve
python -m src.main sync --cwe
python -m src.main sync --kev

# Check sync status
python -m src.main status
```

### Query Examples

```powershell
# Look up specific CVE
python -m src.main query cve CVE-2024-1234

# Find CVEs by CWE
python -m src.main query cwe-cves CWE-79

# Get high-risk CVEs
python -m src.main query high-risk --min-cvss 9.0

# Get only exploited CVEs
python -m src.main query high-risk --kev-only

# Check if CVE is exploited
python -m src.main query is-exploited CVE-2024-1234

# Get recent KEV additions
python -m src.main query kev --days 30

# Get statistics
python -m src.main stats
```

### Programmatic Access

```python
from src.query.api import VulnIntelAPI

# Initialize API
api = VulnIntelAPI()

# Get CVE details
cve = api.get_cve_by_id("CVE-2024-1234")
print(f"CVSS: {cve['cvss_v3_score']}")
print(f"Severity: {cve['cvss_v3_severity']}")

# Check exploit status
if api.is_cve_exploited("CVE-2024-1234"):
    print("⚠️ This CVE is actively exploited!")

# Get high-risk CVEs
high_risk = api.get_high_risk_cves(min_cvss=9.0, kev_only=True)
for cve in high_risk:
    print(f"{cve['cve_id']}: {cve['description'][:100]}...")

# Search by CPE
cves = api.get_cves_for_cpe("cpe:2.3:a:apache:http_server:2.4.49")
print(f"Found {len(cves)} CVEs affecting Apache 2.4.49")
```

---

## Data Sources

| Source | Provider | Format | Update Frequency |
|--------|----------|--------|------------------|
| **CVE** | NIST NVD | JSON 2.0 (gzip) | Every 2-6 hours |
| **CWE** | MITRE | XML (zip) | Weekly |
| **KEV** | CISA | JSON | Daily |

### CVE (Common Vulnerabilities and Exposures)

- **Source:** https://nvd.nist.gov/
- **Feeds:**
  - `nvdcve-1.1-recent.json.gz` (last 8 days)
  - `nvdcve-1.1-modified.json.gz` (incremental updates)
- **Contains:** Vulnerability descriptions, CVSS scores, affected products

### CWE (Common Weakness Enumeration)

- **Source:** https://cwe.mitre.org/
- **Feed:** `cwec_latest.xml.zip`
- **Contains:** Weakness classifications, exploit likelihood, consequences

### KEV (Known Exploited Vulnerabilities)

- **Source:** https://www.cisa.gov/
- **Feed:** `known_exploited_vulnerabilities.json`
- **Contains:** CVEs with confirmed real-world exploitation

---

## Database Schema

### Tables

- **`cve`** — CVE records with CVSS metrics
- **`cwe`** — CWE weakness definitions
- **`kev`** — Known exploited vulnerabilities
- **`cve_cwe_map`** — CVE-to-CWE relationships
- **`sync_metadata`** — Sync status tracking

See `IMPLEMENTATION_PLAN.md` for detailed schema.

---

## Query API Reference

### Core Functions

```python
# Single lookups
get_cve_by_id(cve_id: str) -> Optional[Dict]
get_cwe_by_id(cwe_id: str) -> Optional[Dict]

# CVE searches
get_cves_by_cwe(cwe_id: str, limit: int = 100) -> List[Dict]
get_cves_for_cpe(cpe_string: str, limit: int = 100) -> List[Dict]
get_high_risk_cves(min_cvss: float = 7.0, kev_only: bool = False) -> List[Dict]

# Exploit status
is_cve_exploited(cve_id: str) -> bool
get_kev_entries(days_back: int = 30, ransomware_only: bool = False) -> List[Dict]

# Statistics
get_vuln_stats() -> Dict
```

All functions return JSON-serializable dictionaries.

---

## Integration with PredictPath AI Tools

### Tool 1 (Event Intelligence)
```python
# Enrich log events with CVE data
cve_data = api.get_cve_by_id(detected_cve)
event['cvss_score'] = cve_data['cvss_v3_score']
event['is_exploited'] = api.is_cve_exploited(detected_cve)
```

### Tool 2 (Session Context)
```python
# Amplify risk for exploited vulnerabilities
if api.is_cve_exploited(session_cve):
    risk_score *= 2.0
```

### Tool 3 (Predictive Trajectory)
```python
# Predict attack paths using CWE relationships
cves = api.get_cves_by_cwe("CWE-79")
for cve in cves:
    if api.is_cve_exploited(cve['cve_id']):
        # Prioritize this path
        pass
```

### Tool 4 (Adaptive Decision)
```python
# Recommend patches for KEV CVEs
kev_cves = api.get_kev_entries(days_back=7)
for entry in kev_cves:
    actions.append({
        "type": "patch",
        "cve": entry['cve_id'],
        "urgency": "critical"
    })
```

---

## Automated Scheduling

### Run as Daemon

```powershell
# Sync every hour
python -m src.main daemon --interval 3600
```

### Windows Task Scheduler

```powershell
# Create scheduled task (runs daily at 2 AM)
schtasks /create /tn "VulnIntel Sync" /tr "C:\path\to\.venv\Scripts\python.exe -m src.main sync --all" /sc daily /st 02:00
```

---

## Troubleshooting

### Sync Failures

```powershell
# Check sync status
python -m src.main status

# View logs
type data\logs\vulnintel.log

# Force re-sync
python -m src.main sync --all --force
```

### Database Issues

```powershell
# Reinitialize database (WARNING: deletes all data)
Remove-Item data\db\vuln.db
python -m src.main init
python -m src.main sync --all
```

### Network Issues

- All downloads include retry logic (3 attempts)
- System works offline after initial sync
- Stale data is used if sync fails

---

## Performance

- **Database size:** ~500 MB (after full CVE bootstrap)
- **Sync time:** 3-5 minutes (initial), <1 minute (incremental)
- **Query latency:** <100ms (single lookups), <500ms (complex searches)
- **Memory usage:** <200 MB during sync, <50 MB idle

---

## Security

✅ **Read-only query API** — No write access for consumers  
✅ **Input validation** — All external data sanitized  
✅ **Audit logging** — Full sync history tracked  
✅ **No credentials** — All data sources are public  
✅ **Graceful degradation** — Works with stale data if sync fails

---

## Testing

```powershell
# Run all tests
.\.venv\Scripts\pytest

# Run with coverage
.\.venv\Scripts\pytest --cov=src --cov-report=html

# Run specific test
.\.venv\Scripts\pytest tests/test_cve_ingester.py
```

---

## Directory Structure

```
VulnIntel/
├── src/                    # Source code
│   ├── database/           # SQLite schema and connection
│   ├── ingestors/          # CVE, CWE, KEV ingestors
│   ├── parsers/            # Data parsers
│   ├── query/              # Public API
│   └── utils/              # Utilities
├── data/
│   ├── cache/              # Downloaded files
│   ├── db/                 # vuln.db (SQLite)
│   └── logs/               # Sync logs
├── tests/                  # Unit and integration tests
└── pyproject.toml          # Dependencies
```

---

## Roadmap

- ✅ Phase 1: Foundation (database, config, logging)
- ✅ Phase 2: Ingestors (CVE, CWE, KEV)
- ✅ Phase 3: Parsers (JSON, XML)
- ✅ Phase 4: Query API
- ✅ Phase 5: Automation
- ✅ Phase 6: Testing & Documentation
- 🔄 Phase 7: Historical CVE bootstrap (optional)
- 🔄 Phase 8: REST API wrapper (optional)

---

## License

MIT License — Part of PredictPath AI

---

## Support

For issues or questions, see `IMPLEMENTATION_PLAN.md` or contact the PredictPath AI team.

---

**🛡️ VulnIntel — Intelligence Plumbing for Autonomous Defense**
