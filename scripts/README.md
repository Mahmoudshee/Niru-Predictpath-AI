# PredictPath AI - Vulnerability Scanning Scripts

## Overview

This directory contains production-grade PowerShell scripts for orchestrating enterprise vulnerability scanning tools. All scripts are designed to be deterministic, produce verifiable logs, and integrate seamlessly with the PredictPath AI UI.

## Directory Structure

```
scripts/
├── run-nmap.ps1           # Network reconnaissance & port scanning
├── run-openvas.ps1        # Enterprise vulnerability assessment
├── run-nikto.ps1          # Web server vulnerability scanning
├── run-nuclei.ps1         # CVE-based template scanning
└── run-network-scan.ps1   # Master orchestrator (UI trigger point)

logs/
├── nmap/                  # Nmap XML and text outputs
├── openvas/               # OpenVAS XML reports
├── nikto/                 # Nikto XML and text outputs
└── nuclei/                # Nuclei JSON and text outputs
```

## Scripts

### 1. `run-nmap.ps1` — Network Reconnaissance

**Purpose**: Comprehensive network scanning with Nmap

**Features**:
- Host discovery (`-sn`)
- SYN stealth scan (`-sS`)
- Service/version detection (`-sV`)
- OS fingerprinting (`-O`)
- Vulnerability scripts (`--script vuln`)
- Aggressive timing (`-T4`)

**Usage**:
```powershell
.\scripts\run-nmap.ps1 -Target "192.168.1.0/24"
```

**Output**:
- `logs/nmap/nmap-YYYYMMDD-HHMMSS.xml`
- `logs/nmap/nmap-YYYYMMDD-HHMMSS.txt`

**Requirements**:
- Nmap installed: https://nmap.org/download.html

---

### 2. `run-openvas.ps1` — Vulnerability Assessment

**Purpose**: Enterprise-grade vulnerability scanning with OpenVAS/GVM

**Features**:
- CVE-backed vulnerability detection
- Full and Fast scan configuration
- Progress monitoring (30-second polls)
- Docker-based execution

**Usage**:
```powershell
.\scripts\run-openvas.ps1 -Target "192.168.1.0/24"
```

**Output**:
- `logs/openvas/openvas-YYYYMMDD-HHMMSS.xml`

**Requirements**:
- Docker installed and running
- OpenVAS container: `docker run -d -p 443:443 --name openvas mikesplain/openvas`

**Note**: Initial scan may take 15-60 minutes depending on target size.

---

### 3. `run-nikto.ps1` — Web Vulnerability Scanning

**Purpose**: Web server and application security assessment

**Features**:
- Server misconfiguration detection
- Outdated software identification
- Dangerous files/CGI detection
- SSL/TLS configuration checks

**Usage**:
```powershell
.\scripts\run-nikto.ps1 -Target "http://192.168.1.100" -Port 80
.\scripts\run-nikto.ps1 -Target "https://example.com" -Port 443 -SSL
```

**Output**:
- `logs/nikto/nikto-YYYYMMDD-HHMMSS.xml`
- `logs/nikto/nikto-YYYYMMDD-HHMMSS.txt`

**Requirements**:
- Docker installed
- Nikto image: `docker pull securecodebox/nikto`

---

### 4. `run-nuclei.ps1` — CVE Template Scanning

**Purpose**: Template-based vulnerability detection with CVE coverage

**Features**:
- CVE-based vulnerability detection
- Misconfiguration identification
- Exposed panels and services
- Security headers analysis
- Technology detection

**Usage**:
```powershell
.\scripts\run-nuclei.ps1 -Target "http://192.168.1.100"
.\scripts\run-nuclei.ps1 -Target "https://example.com" -Severity "critical,high"
.\scripts\run-nuclei.ps1 -Target "http://example.com" -UpdateTemplates
```

**Output**:
- `logs/nuclei/nuclei-YYYYMMDD-HHMMSS.json`
- `logs/nuclei/nuclei-YYYYMMDD-HHMMSS.txt`

**Requirements**:
- Nuclei installed: https://github.com/projectdiscovery/nuclei
- OR Docker: `docker pull projectdiscovery/nuclei`

---

### 5. `run-network-scan.ps1` — Master Orchestrator

**Purpose**: Coordinate all vulnerability scanning tools in a single workflow

**Features**:
- Sequential execution of all scanners
- Progress tracking and status reporting
- Comprehensive summary generation
- Flexible scan configuration

**Usage**:
```powershell
# Full scan (network + web)
.\scripts\run-network-scan.ps1 -Target "192.168.1.0/24" -WebTarget "http://192.168.1.100"

# Network only (skip web scans)
.\scripts\run-network-scan.ps1 -Target "192.168.1.0/24"

# Quick scan (skip OpenVAS)
.\scripts\run-network-scan.ps1 -Target "192.168.1.0/24" -QuickScan

# Custom configuration
.\scripts\run-network-scan.ps1 -Target "192.168.1.0/24" -SkipOpenVAS -SkipNikto
```

**Output**:
- All individual tool logs (see above)
- `logs/scan-summary-YYYYMMDD-HHMMSS.txt` (consolidated summary)

**This is the script triggered by the UI "Network Security Analysis" button.**

---

## Installation & Setup

### Prerequisites

1. **PowerShell 5.1+** (Windows) or **PowerShell Core 7+** (cross-platform)
2. **Docker Desktop** (for OpenVAS, Nikto, Nuclei)
3. **Nmap** (native installation recommended)

### Quick Start

```powershell
# 1. Navigate to project root
cd c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools

# 2. Create log directories (auto-created by scripts)
New-Item -ItemType Directory -Path "logs\nmap", "logs\openvas", "logs\nikto", "logs\nuclei" -Force

# 3. Pull Docker images
docker pull mikesplain/openvas
docker pull securecodebox/nikto
docker pull projectdiscovery/nuclei

# 4. Start OpenVAS container (one-time setup)
docker run -d -p 443:443 --name openvas mikesplain/openvas

# 5. Run a test scan
.\scripts\run-network-scan.ps1 -Target "127.0.0.1" -QuickScan
```

---

## Integration with UI

The UI triggers scans via the master orchestrator:

```typescript
// In your React component
const runNetworkScan = async (target: string, webTarget?: string) => {
  const command = webTarget 
    ? `.\scripts\run-network-scan.ps1 -Target "${target}" -WebTarget "${webTarget}"`
    : `.\scripts\run-network-scan.ps1 -Target "${target}"`;
  
  // Execute via your PowerShell terminal integration
  await executePowerShellCommand(command);
};
```

All terminal output is streamed live to the UI, and logs are available for download upon completion.

---

## Troubleshooting

### Nmap not found
```powershell
# Install Nmap from https://nmap.org/download.html
# Add to PATH: C:\Program Files (x86)\Nmap
```

### Docker not running
```powershell
# Start Docker Desktop
# Verify: docker ps
```

### OpenVAS container not responding
```powershell
# Restart container
docker restart openvas

# Check logs
docker logs openvas

# Recreate if needed
docker rm -f openvas
docker run -d -p 443:443 --name openvas mikesplain/openvas
```

### Nuclei templates outdated
```powershell
.\scripts\run-nuclei.ps1 -Target "http://example.com" -UpdateTemplates
```

---

## Security Considerations

⚠️ **Important**:
- These scripts perform **active scanning** which may be detected by IDS/IPS
- Always obtain **written authorization** before scanning networks you don't own
- Some scans (especially OpenVAS) can be **disruptive** to production systems
- Use `-QuickScan` flag for less invasive reconnaissance

---

## Next Steps

After successful scan execution:
1. **Parse logs** for vulnerability extraction
2. **Map CVEs** to MITRE ATT&CK techniques
3. **Calculate risk scores** using CVSS
4. **Generate remediation playbooks**
5. **Integrate with SIEM** for continuous monitoring

---

## License

Part of the PredictPath AI cybersecurity platform.

For questions or issues, refer to the main project README.
