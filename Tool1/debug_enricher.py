from src.processing.enricher import Enricher
import logging
import time

logging.basicConfig(level=logging.DEBUG)
print("Initializing Enricher...")
start = time.time()
try:
    e = Enricher()
    print(f"Enricher initialized in {time.time() - start:.2f}s")
    res = e.infer_mitre("LogOn failure")
    print("Inference result:", res)
except Exception as e:
    print(f"Enricher Check Failed: {e}")
