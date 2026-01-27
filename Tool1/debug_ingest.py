from src.ingestion.auth_lanl import LanlAuthIngestor
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
path = Path("data/samples/lanl_small.txt")
print(f"File exists: {path.exists()}")
print(f"Content:\n{path.read_text()}")

try:
    ingestor = LanlAuthIngestor(path)
    count = 0
    for r in ingestor.ingest():
        print("Record:", r)
        count += 1
    print(f"Total: {count}")
except Exception as e:
    print(f"Error: {e}")
