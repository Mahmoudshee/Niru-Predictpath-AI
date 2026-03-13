import json
import csv
import struct
from pathlib import Path
from typing import Generator, Dict, Any, Optional
from .base import BaseIngestor
import logging

logger = logging.getLogger(__name__)

# All Wazuh report top-level category keys that contain arrays of events
WAZUH_CATEGORY_KEYS = [
    "malware_behavior",
    "vulnerability",
    "privilege_escalation",
    "persistence",
    "data",
    "events",
    "alerts",
    "hits",
]

class UniversalIngestor(BaseIngestor):
    """
    Streaming ingestor for JSON, NDJSON, CSV, Parquet, XML (Nmap/generic),
    PCAP/PCAPNG (binary packet captures), and raw text/log files.
    Implements runtime schema inference hints.
    Supports ALL log file extensions without crashing.
    """

    def ingest(self) -> Generator[Dict[str, Any], None, None]:
        suffix = self.file_path.suffix.lower()
        logger.info(f"Streaming from {self.file_path} (Format: {suffix})")

        try:
            if suffix == '.json':
                yield from self._ingest_json()
            elif suffix in ['.ndjson', '.log', '.txt']:
                yield from self._ingest_ndjson()
            elif suffix == '.csv':
                yield from self._ingest_csv()
            elif suffix == '.parquet':
                yield from self._ingest_parquet()
            elif suffix == '.xml':
                yield from self._ingest_xml()
            elif suffix in ['.pcap', '.pcapng', '.cap']:
                yield from self._ingest_pcap()
            elif suffix in ['.gz', '.gzip']:
                yield from self._ingest_gzip()
            else:
                # Attempt smart detection: try JSON first, then NDJSON, then raw
                yield from self._ingest_smart_detect()
        except Exception as e:
            logger.error(f"Ingestion failed for {self.file_path}: {e}")
            # Emit at least one record so the pipeline doesn't silently produce nothing
            yield {
                "raw_text": f"Ingestion error for {self.file_path.name}: {e}",
                "_parsing_type": "ingestion_error",
                "source_host": "unknown",
            }

    def _ingest_json(self):
        with open(self.file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            try:
                data = json.load(f)
                yielded_count = 0

                # ── CASE 1: ZAP Report ──────────────────────────────────────
                # ZAP: { "site": [ { "alerts": [...] } ] }
                if isinstance(data, dict) and "site" in data and isinstance(data["site"], list):
                    for site in data["site"]:
                        if isinstance(site, dict) and "alerts" in site and isinstance(site["alerts"], list):
                            logger.info(f"Detected ZAP report for {site.get('@name', 'site')}")
                            for alert_type in site["alerts"]:
                                instances = alert_type.get("instances", [])
                                if not instances:
                                    yield alert_type
                                    yielded_count += 1
                                    continue
                                for inst in instances:
                                    event = alert_type.copy()
                                    event.pop("instances", None)
                                    event.update(inst)
                                    yield event
                                    yielded_count += 1
                    if yielded_count > 0:
                        return

                # ── CASE 2: Wazuh / Generic Multi-Category Report ─────────
                # Structure: { "category_name": [ {...}, {...} ], ... }
                # We iterate ALL top-level keys that contain lists of dicts
                if isinstance(data, dict):
                    for key in WAZUH_CATEGORY_KEYS:
                        target_data = data.get(key)
                        if not target_data:
                            continue

                        # Handle Elasticsearch hits.hits
                        if key == "hits" and isinstance(target_data, dict) and "hits" in target_data:
                            target_data = target_data["hits"]

                        if isinstance(target_data, list) and len(target_data) > 0:
                            logger.info(f"Auto-flattening report array: '{key}' ({len(target_data)} events)")
                            for item in target_data:
                                if isinstance(item, dict):
                                    # Tag each item with its category for downstream use
                                    tagged = dict(item)
                                    tagged.setdefault("_wazuh_category", key)
                                    if isinstance(item, dict) and "_source" in item:
                                        yield item["_source"]
                                    else:
                                        yield tagged
                                    yielded_count += 1
                                else:
                                    # Scalar item in list → wrap
                                    yield {"raw_text": str(item), "_wazuh_category": key}
                                    yielded_count += 1

                    if yielded_count > 0:
                        return

                    # ── CASE 3: Plain dict with no known top-level list keys ──
                    # Scan ALL top-level keys for list-of-dicts
                    for key, val in data.items():
                        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                            logger.info(f"Auto-discovered event array under key '{key}' ({len(val)} items)")
                            for item in val:
                                yield item
                                yielded_count += 1
                    if yielded_count > 0:
                        return

                    # ── CASE 4: Single dict record ────────────────────────────
                    yield data
                    return

                # ── CASE 5: Top-level list ────────────────────────────────────
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            yield item
                        else:
                            yield {"raw_text": str(item), "_parsing_type": "list_scalar"}
                    return

                # Fallback: yield raw
                yield {"raw_text": str(data), "_parsing_type": "json_scalar"}

            except json.JSONDecodeError:
                # Fallback to NDJSON if single object parse fails
                f.seek(0)
                yield from self._ingest_ndjson_from_file(f)

    def _get_nested(self, data: Dict[str, Any], key_path: str) -> Any:
        """Helper to get value from nested dict using dot notation."""
        parts = key_path.split(".")
        curr = data
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return None
        return curr

    def _ingest_ndjson(self):
        with open(self.file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            yield from self._ingest_ndjson_from_file(f)

    def _ingest_ndjson_from_file(self, f):
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
                else:
                    yield {"raw_text": str(obj), "_parsing_type": "ndjson_scalar"}
            except json.JSONDecodeError:
                yield {"raw_text": line, "_parsing_type": "raw_log"}

    def _ingest_csv(self):
        with open(self.file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield dict(row)

    def _ingest_parquet(self):
        import polars as pl
        df = pl.scan_parquet(str(self.file_path))
        for row in df.collect().iter_rows(named=True):
            yield row

    def _ingest_xml(self):
        """
        Parse XML output into structured events.
        Handles Nmap XML specifically, and generic XML as a fallback.
        Each open port on each host becomes one event dict.
        """
        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(str(self.file_path))
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            yield {"raw_text": str(self.file_path.name), "_parsing_type": "xml_parse_error"}
            return

        # Detect Nmap XML
        if root.tag == "nmaprun" or root.find("host") is not None:
            yield from self._parse_nmap_xml(root)
            return

        # Generic XML: yield each child element as a flat dict
        yielded = 0
        for child in root:
            record = {"_xml_tag": child.tag}
            record.update(child.attrib)
            # Add text content if present
            if child.text and child.text.strip():
                record["raw_text"] = child.text.strip()
            # Add sub-children as string values
            for sub in child:
                record[sub.tag] = sub.text or sub.get("name", "")
            yield record
            yielded += 1

        if yielded == 0:
            yield {
                "raw_text": f"XML file parsed but no records found: {self.file_path.name}",
                "_parsing_type": "xml_empty",
            }

    def _parse_nmap_xml(self, root):
        """Parse Nmap XML structure into port/host events."""
        scan_args = root.get("args", "nmap")
        scan_start = root.get("startstr", "")
        yielded = 0

        for host in root.findall("host"):
            addr_el = host.find("address")
            ip = addr_el.get("addr", "unknown") if addr_el is not None else "unknown"

            hostname = ip
            hostnames_el = host.find("hostnames")
            if hostnames_el is not None:
                hn_el = hostnames_el.find("hostname")
                if hn_el is not None:
                    hostname = hn_el.get("name", ip)

            status_el = host.find("status")
            host_state = status_el.get("state", "unknown") if status_el is not None else "unknown"

            os_match = ""
            os_el = host.find("os")
            if os_el is not None:
                osmatch = os_el.find("osmatch")
                if osmatch is not None:
                    os_match = osmatch.get("name", "")

            ports_el = host.find("ports")
            if ports_el is None:
                yield {
                    "source_host": ip,
                    "hostname": hostname,
                    "host_state": host_state,
                    "os": os_match,
                    "port": None,
                    "protocol": "icmp",
                    "service_name": "host_discovery",
                    "service_product": "",
                    "port_state": host_state,
                    "scan_args": scan_args,
                    "scan_start": scan_start,
                    "raw_text": f"Nmap host {ip} ({hostname}) is {host_state}",
                    "_parsing_type": "nmap_host",
                }
                yielded += 1
                continue

            for port_el in ports_el.findall("port"):
                port_num = port_el.get("portid", "0")
                proto = port_el.get("protocol", "tcp")

                state_el = port_el.find("state")
                port_state = state_el.get("state", "unknown") if state_el is not None else "unknown"

                svc_el = port_el.find("service")
                svc_name = svc_product = svc_version = svc_extra = ""
                if svc_el is not None:
                    svc_name = svc_el.get("name", "")
                    svc_product = svc_el.get("product", "")
                    svc_version = svc_el.get("version", "")
                    svc_extra = svc_el.get("extrainfo", "")

                script_outputs = []
                for script_el in port_el.findall("script"):
                    sid = script_el.get("id", "")
                    out = script_el.get("output", "")
                    script_outputs.append(f"{sid}: {out}")

                raw_desc = (
                    f"Nmap: {ip}:{port_num}/{proto} {port_state} - "
                    f"{svc_product} {svc_version} ({svc_name}) {svc_extra}"
                )
                if script_outputs:
                    raw_desc += " | Scripts: " + "; ".join(script_outputs[:3])

                yield {
                    "source_host": ip,
                    "hostname": hostname,
                    "host_state": host_state,
                    "os": os_match,
                    "port": port_num,
                    "protocol": proto,
                    "service_name": svc_name,
                    "service_product": svc_product,
                    "service_version": svc_version,
                    "port_state": port_state,
                    "script_output": "; ".join(script_outputs),
                    "scan_args": scan_args,
                    "scan_start": scan_start,
                    "raw_text": raw_desc,
                    "_parsing_type": "nmap_port",
                }
                yielded += 1

        if yielded == 0:
            yield {
                "raw_text": f"Nmap XML parsed but no hosts/ports found in {self.file_path.name}",
                "_parsing_type": "nmap_empty",
            }
        else:
            logger.info(f"Nmap XML: yielded {yielded} port/host events from {self.file_path.name}")

    def _ingest_pcap(self):
        """
        Handle PCAP / PCAPNG binary packet captures.
        Attempts to use scapy if available, otherwise yields metadata-only records.
        """
        logger.info(f"Processing PCAP/PCAPNG: {self.file_path.name}")

        # Try using scapy for rich data
        try:
            from scapy.all import rdpcap, IP, TCP, UDP, ICMP
            packets = rdpcap(str(self.file_path))
            logger.info(f"Scapy loaded {len(packets)} packets from {self.file_path.name}")
            yielded = 0
            for i, pkt in enumerate(packets):
                try:
                    record = {
                        "_parsing_type": "pcap_packet",
                        "raw_text": pkt.summary(),
                        "protocol": "unknown",
                    }
                    if IP in pkt:
                        record["source_host"] = pkt[IP].src
                        record["target_host"] = pkt[IP].dst
                        record["protocol"] = "ip"
                    if TCP in pkt:
                        record["port"] = str(pkt[TCP].dport)
                        record["protocol"] = "tcp"
                        record["raw_text"] = f"TCP {pkt[IP].src}:{pkt[TCP].sport} -> {pkt[IP].dst}:{pkt[TCP].dport}"
                    elif UDP in pkt:
                        record["port"] = str(pkt[UDP].dport)
                        record["protocol"] = "udp"
                        record["raw_text"] = f"UDP {pkt[IP].src}:{pkt[UDP].sport} -> {pkt[IP].dst}:{pkt[UDP].dport}"
                    elif ICMP in pkt:
                        record["protocol"] = "icmp"
                    yield record
                    yielded += 1
                except Exception:
                    continue
            if yielded == 0:
                yield {"raw_text": f"PCAP: no parseable packets in {self.file_path.name}", "_parsing_type": "pcap_empty"}
            return
        except ImportError:
            logger.warning("scapy not installed; falling back to PCAP header-only parsing")
        except Exception as e:
            logger.warning(f"scapy failed to read PCAP: {e}; falling back to header-only parsing")

        # Fallback: parse PCAP/PCAPNG global header manually
        try:
            with open(self.file_path, 'rb') as f:
                header = f.read(24)
                if len(header) < 24:
                    yield {"raw_text": f"PCAP file too small: {self.file_path.name}", "_parsing_type": "pcap_error"}
                    return

                magic = struct.unpack('<I', header[:4])[0]
                is_pcap = magic in (0xA1B2C3D4, 0xD4C3B2A1, 0xA1B23C4D, 0x4D3CB2A1)
                is_pcapng = magic == 0x0A0D0D0A

                if is_pcap:
                    yield {
                        "raw_text": f"PCAP capture file: {self.file_path.name} (use scapy for full packet data)",
                        "_parsing_type": "pcap_header",
                        "protocol": "pcap",
                        "source_host": "pcap_file",
                    }
                elif is_pcapng:
                    yield {
                        "raw_text": f"PCAPNG capture file: {self.file_path.name} (use scapy for full packet data)",
                        "_parsing_type": "pcapng_header",
                        "protocol": "pcapng",
                        "source_host": "pcapng_file",
                    }
                else:
                    # Unknown binary format - treat as raw
                    yield {
                        "raw_text": f"Unknown binary format (magic=0x{magic:08X}): {self.file_path.name}",
                        "_parsing_type": "binary_unknown",
                        "source_host": "binary_file",
                    }
        except Exception as e:
            yield {"raw_text": f"PCAP parse error: {e}", "_parsing_type": "pcap_error"}

    def _ingest_gzip(self):
        """Handle .gz compressed files by detecting and decompressing."""
        import gzip
        try:
            with gzip.open(str(self.file_path), 'rt', encoding='utf-8', errors='replace') as f:
                # Try JSON first
                content = f.read()
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        yield item if isinstance(item, dict) else {"raw_text": str(item)}
                elif isinstance(data, dict):
                    yield data
            except json.JSONDecodeError:
                # Treat as NDJSON / raw log lines
                for line in content.splitlines():
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            yield {"raw_text": line.strip(), "_parsing_type": "gz_raw"}
        except Exception as e:
            logger.error(f"Failed to read gzip file: {e}")
            yield {"raw_text": f"Gzip read error: {e}", "_parsing_type": "gz_error"}

    def _ingest_smart_detect(self):
        """Try to auto-detect format for files with unknown extensions."""
        # Peek at first few bytes
        try:
            with open(self.file_path, 'rb') as f:
                first_bytes = f.read(8)

            # PCAP magic
            if len(first_bytes) >= 4:
                magic = struct.unpack('<I', first_bytes[:4])[0]
                if magic in (0xA1B2C3D4, 0xD4C3B2A1, 0xA1B23C4D, 0x4D3CB2A1, 0x0A0D0D0A):
                    yield from self._ingest_pcap()
                    return

            # Try text: JSON, then NDJSON, then raw
            try:
                with open(self.file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                    first_char = f.read(1).strip()
                if first_char in ('{', '['):
                    yield from self._ingest_json()
                    return
                else:
                    # Try as NDJSON / raw log
                    yield from self._ingest_ndjson()
                    return
            except UnicodeDecodeError:
                pass

            # Binary fallback
            yield {
                "raw_text": f"Unrecognized binary file: {self.file_path.name}",
                "_parsing_type": "binary_unknown",
                "source_host": "binary_file",
            }
        except Exception as e:
            logger.error(f"Smart detect failed: {e}")
            yield {"raw_text": f"Smart detect error: {e}", "_parsing_type": "detect_error"}

    def _ingest_raw(self):
        with open(self.file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                if line.strip():
                    yield {"raw_text": line.strip(), "_parsing_type": "raw_text"}

    def estimate_count(self) -> int:
        try:
            return sum(1 for _ in open(self.file_path, 'rb'))
        except Exception:
            return 0
