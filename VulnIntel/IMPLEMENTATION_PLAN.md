# Vulnerability Intelligence Data Pipeline - Implementation Plan

## Executive Summary

This document outlines the complete implementation of a standalone, production-ready vulnerability intelligence subsystem for PredictPath AI. The system will ingest, normalize, and store CVE, CWE, and KEV data from authoritative sources, providing clean query interfaces for future tool integration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Vulnerability Intelligence                  │
│                      Data Pipeline                           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │   CVE   │          │   CWE   │          │   KEV   │
   │ Ingester│          │ Ingester│          │ Ingester│
   └────┬────┘          └────┬────┘          └────┬────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                     ┌────────▼────────┐
                     │  SQLite Storage │
                     │   (vuln.db)     │
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │  Query Interface│
                     │   (Python API)  │
                     └─────────────────┘
```

---

## Directory Structure

```
VulnIntel/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py           # SQLite schema definitions
│   │   └── connection.py       # Database connection manager
│   ├── ingestors/
│   │   ├── __init__.py
│   │   ├── base.py             # Base ingestion class
│   │   ├── cve_ingester.py     # NVD CVE ingestion
│   │   ├── cwe_ingester.py     # MITRE CWE ingestion
│   │   └── kev_ingester.py     # CISA KEV ingestion
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── cve_parser.py       # NVD JSON 2.0 parser
│   │   ├── cwe_parser.py       # CWE XML parser
│   │   └── kev_parser.py       # KEV JSON parser
│   ├── query/
│   │   ├── __init__.py
│   │   └── api.py              # Public query interface
│   └── utils/
│       ├── __init__.py
│       ├── downloader.py       # HTTP download with retry
│       ├── logger.py           # Logging configuration
│       └── validators.py       # Data validation utilities
├── data/
│   ├── cache/                  # Downloaded raw files
│   ├── db/                     # SQLite database
│   └── logs/                   # Ingestion logs
├── tests/
│   ├── __init__.py
│   ├── test_cve_ingester.py
│   ├── test_cwe_ingester.py
│   ├── test_kev_ingester.py
│   └── test_query_api.py
├── pyproject.toml              # Dependencies and metadata
├── README.md                   # User documentation
└── IMPLEMENTATION_PLAN.md      # This file
```

---

## Database Schema

### Table: `cve`

```sql
CREATE TABLE cve (
    cve_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    published_date TEXT NOT NULL,
    last_modified_date TEXT NOT NULL,
    cvss_v3_score REAL,
    cvss_v3_severity TEXT,
    cvss_v3_vector TEXT,
    attack_vector TEXT,
    attack_complexity TEXT,
    privileges_required TEXT,
    user_interaction TEXT,
    scope TEXT,
    confidentiality_impact TEXT,
    integrity_impact TEXT,
    availability_impact TEXT,
    affected_cpes TEXT,          -- JSON array
    references TEXT,             -- JSON array
    source_feed TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_cve_published ON cve(published_date);
CREATE INDEX idx_cve_modified ON cve(last_modified_date);
CREATE INDEX idx_cve_severity ON cve(cvss_v3_severity);
CREATE INDEX idx_cve_score ON cve(cvss_v3_score);
```

### Table: `cwe`

```sql
CREATE TABLE cwe (
    cwe_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    abstraction TEXT,
    status TEXT,
    likelihood_of_exploit TEXT,
    common_consequences TEXT,    -- JSON array
    applicable_platforms TEXT,   -- JSON array
    modes_of_introduction TEXT,  -- JSON array
    detection_methods TEXT,      -- JSON array
    ingested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_cwe_abstraction ON cwe(abstraction);
CREATE INDEX idx_cwe_likelihood ON cwe(likelihood_of_exploit);
```

### Table: `kev`

```sql
CREATE TABLE kev (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cve_id TEXT NOT NULL,
    vendor_project TEXT,
    product TEXT,
    vulnerability_name TEXT,
    date_added TEXT NOT NULL,
    short_description TEXT,
    required_action TEXT,
    due_date TEXT,
    known_ransomware_use TEXT,
    notes TEXT,
    ingested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (cve_id) REFERENCES cve(cve_id)
);

CREATE INDEX idx_kev_cve ON kev(cve_id);
CREATE INDEX idx_kev_date_added ON kev(date_added);
CREATE INDEX idx_kev_ransomware ON kev(known_ransomware_use);
```

### Table: `cve_cwe_map`

```sql
CREATE TABLE cve_cwe_map (
    cve_id TEXT NOT NULL,
    cwe_id TEXT NOT NULL,
    PRIMARY KEY (cve_id, cwe_id),
    FOREIGN KEY (cve_id) REFERENCES cve(cve_id),
    FOREIGN KEY (cwe_id) REFERENCES cwe(cwe_id)
);

CREATE INDEX idx_map_cve ON cve_cwe_map(cve_id);
CREATE INDEX idx_map_cwe ON cve_cwe_map(cwe_id);
```

### Table: `sync_metadata`

```sql
CREATE TABLE sync_metadata (
    source TEXT PRIMARY KEY,
    last_sync_time TEXT NOT NULL,
    last_sync_status TEXT NOT NULL,
    records_processed INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    next_sync_due TEXT
);
```

---

## Data Sources & Update Strategy

### CVE (NVD JSON 2.0)

**Sources:**
- Initial: `https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz`
- Modified: `https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.gz`
- Historical (optional): `https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz`

**Update Frequency:** Every 2-6 hours  
**Strategy:**
1. Bootstrap: Download recent feed (last 8 days)
2. Incremental: Download modified feed
3. Upsert logic: Update if `lastModifiedDate` is newer

### CWE (MITRE XML)

**Source:**
- `https://cwe.mitre.org/data/xml/cwec_latest.xml.zip`

**Update Frequency:** Weekly  
**Strategy:**
1. Download and extract XML
2. Parse all weakness entries
3. Full replace (CWE is relatively static)

### KEV (CISA JSON)

**Source:**
- `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`

**Update Frequency:** Daily  
**Strategy:**
1. Download JSON
2. Upsert based on CVE ID
3. Track `dateAdded` for new exploits

---

## Query Interface (Public API)

### Core Functions

```python
# Single CVE lookup
def get_cve_by_id(cve_id: str) -> Optional[Dict[str, Any]]

# CVEs by weakness
def get_cves_by_cwe(cwe_id: str, limit: int = 100) -> List[Dict[str, Any]]

# Exploit status check
def is_cve_exploited(cve_id: str) -> bool

# High-risk CVEs
def get_high_risk_cves(
    min_cvss: float = 7.0,
    kev_only: bool = False,
    limit: int = 100
) -> List[Dict[str, Any]]

# CPE-based search
def get_cves_for_cpe(cpe_string: str, limit: int = 100) -> List[Dict[str, Any]]

# CWE lookup
def get_cwe_by_id(cwe_id: str) -> Optional[Dict[str, Any]]

# KEV entries
def get_kev_entries(
    days_back: int = 30,
    ransomware_only: bool = False
) -> List[Dict[str, Any]]

# Statistics
def get_vuln_stats() -> Dict[str, Any]
```

---

## Implementation Phases

### Phase 1: Foundation (Days 1-2)
- ✅ Create directory structure
- ✅ Set up `pyproject.toml` with dependencies
- ✅ Implement database schema
- ✅ Create configuration management
- ✅ Set up logging infrastructure

### Phase 2: Ingestors (Days 3-5)
- ✅ Implement base ingestion class
- ✅ Build CVE ingester (NVD JSON 2.0)
- ✅ Build CWE ingester (XML parsing)
- ✅ Build KEV ingester (JSON parsing)
- ✅ Add retry logic and error handling

### Phase 3: Parsers (Days 6-7)
- ✅ CVE JSON 2.0 parser with CVSS extraction
- ✅ CWE XML parser with relationship mapping
- ✅ KEV JSON parser with validation
- ✅ Data normalization utilities

### Phase 4: Query Interface (Days 8-9)
- ✅ Implement all query functions
- ✅ Add result caching (optional)
- ✅ Create JSON serialization helpers
- ✅ Document API usage

### Phase 5: Automation & Scheduling (Day 10)
- ✅ CLI commands for manual sync
- ✅ Sync status reporting
- ✅ Automated scheduling logic
- ✅ Health check endpoints

### Phase 6: Testing & Documentation (Days 11-12)
- ✅ Unit tests for all components
- ✅ Integration tests
- ✅ Performance benchmarks
- ✅ Complete README with examples

---

## CLI Interface

```bash
# Initialize database
python -m src.main init

# Sync all sources
python -m src.main sync --all

# Sync specific source
python -m src.main sync --cve
python -m src.main sync --cwe
python -m src.main sync --kev

# Query examples
python -m src.main query cve CVE-2024-1234
python -m src.main query cwe CWE-79
python -m src.main query high-risk --min-cvss 9.0 --kev-only

# Status and statistics
python -m src.main status
python -m src.main stats

# Scheduled sync (runs in background)
python -m src.main daemon --interval 3600
```

---

## Dependencies

```toml
[project]
name = "vulnintel"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    "requests>=2.31.0",
    "urllib3>=2.0.0",
    "lxml>=5.0.0",
    "python-dateutil>=2.8.0",
    "schedule>=1.2.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
]
```

---

## Security Considerations

1. **Read-Only Access**: Query API provides read-only access
2. **Write Protection**: Only ingestion pipeline can write to DB
3. **Input Validation**: All external data validated before storage
4. **Logging**: Full audit trail of all sync operations
5. **Graceful Degradation**: System continues with stale data if sync fails
6. **No Credentials**: All data sources are public (no API keys needed)

---

## Integration with Existing Tools

### Tool 1 (Event Intelligence)
- Query CVE details for vulnerability mentions in logs
- Enrich events with CVSS scores and exploit status

### Tool 2 (Session Context)
- Check if detected vulnerabilities are in KEV
- Amplify risk scores for exploited CVEs

### Tool 3 (Predictive Trajectory)
- Use CWE relationships to predict attack chains
- Prioritize paths involving KEV-listed vulnerabilities

### Tool 4 (Adaptive Decision)
- Recommend patches for high-CVSS, KEV-listed CVEs
- Suggest compensating controls based on CWE data

### Tool 5 (Response Execution)
- Block traffic to systems with critical KEV CVEs
- Apply emergency patches for actively exploited vulnerabilities

### Tool 6 (Governance)
- Track effectiveness of vulnerability-based decisions
- Learn which CVSS thresholds trigger best outcomes

---

## Success Metrics

- ✅ CVE database contains >200,000 entries
- ✅ CWE catalog fully imported (~900 entries)
- ✅ KEV list updated daily (currently ~1,100 entries)
- ✅ Sync operations complete in <5 minutes
- ✅ Query response time <100ms for single lookups
- ✅ Zero data loss during incremental updates
- ✅ System operates offline after initial sync
- ✅ All queries return JSON-serializable results

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create virtual environment** and install dependencies
3. **Implement Phase 1** (foundation)
4. **Test database schema** with sample data
5. **Build ingestors** incrementally
6. **Validate with real data** from NVD, MITRE, CISA
7. **Document integration points** for Tools 1-6
8. **Deploy and monitor** first sync cycle

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-06  
**Status:** Ready for Implementation
