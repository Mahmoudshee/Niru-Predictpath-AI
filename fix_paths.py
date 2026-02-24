import re

# Read the file
with open(r"c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\predictpath-ui\backend\main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace all log paths
content = content.replace('os.path.join(TOOLS_ROOT, "Tool1", "data", "uploads")', 'os.path.join(TOOLS_ROOT, "scripts", "saved-logs")')
content = content.replace('os.path.join(TOOLS_ROOT, "logs", "nmap")', 'os.path.join(TOOLS_ROOT, "scripts", "saved-logs", "nmap")')
content = content.replace('os.path.join(TOOLS_ROOT, "logs", "openvas")', 'os.path.join(TOOLS_ROOT, "scripts", "saved-logs", "openvas")')
content = content.replace('os.path.join(logs_dir, "nmap")', 'os.path.join(TOOLS_ROOT, "scripts", "saved-logs", "nmap")')
content = content.replace('os.path.join(logs_dir, "openvas")', 'os.path.join(TOOLS_ROOT, "scripts", "saved-logs", "openvas")')
content = content.replace('os.path.join(TOOLS_ROOT, "logs", scan_type)', 'os.path.join(TOOLS_ROOT, "scripts", "saved-logs", scan_type)')

# Fix delete validation
content = re.sub(
    r'logs_dir = os\.path\.join\(TOOLS_ROOT, "logs"\)\s+if not abs_path\.startswith\(logs_dir\):',
    'saved_logs_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs")\n    \n    if not abs_path.startswith(saved_logs_dir):',
    content
)

# Write back
with open(r"c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\predictpath-ui\backend\main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed all paths to use scripts/saved-logs")
