#!/bin/bash
set -e
# Warm up sudo with the provided password
echo 'kenty1234' | sudo -S ls > /dev/null

START=$(cat /opt/predictpath/wazuh_scan_start.txt)
echo "Filtering events since: $START"

# Create output dir with sudo
echo 'kenty1234' | sudo -S mkdir -p /opt/predictpath
echo 'kenty1234' | sudo -S chmod 777 /opt/predictpath

# Run JQ with sudo to read ossec logs
# Wazuh alerts.json is NDJSON (line-delimited). We use a two-stage filter:
# 1. Filter lines strictly by timestamp (fast, stream processing)
# 2. Slurp only the relevant events into memory for grouping
echo 'kenty1234' | sudo -S cat /var/ossec/logs/alerts/alerts.json | jq -c --arg start "$START" '
  select(.timestamp > $start)
' | jq -s '
  {
    vulnerability: map(select(.rule.groups | index("vulnerability"))),
    malware_behavior: map(select(.rule.groups | (index("malware") or index("rootcheck") or index("syscheck")))),
    privilege_escalation: map(select(.rule.groups | (index("sudo") or index("authentication")))),
    persistence: map(select(.rule.groups | (index("startup") or index("service") or index("rootcheck"))))
  }
' > /opt/predictpath/final_report.json

# Ensure output is readable by normal user
echo 'kenty1234' | sudo -S chmod 644 /opt/predictpath/final_report.json