import polars as pl

path = r"c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\Tool1\data\output\2026-02-20\events_2026-02-20_1771559572.989196.parquet"

df = pl.read_parquet(path)
print(f"Total events: {len(df)}")

if "observed_cve_ids" in df.columns:
    cve_detects = df.filter(pl.col("observed_cve_ids").list.len() > 0)
    print(f"Events with CVEs: {len(cve_detects)}")
    if len(cve_detects) > 0:
        print(cve_detects.select(["observed_cve_ids"]).head())
else:
    print("observed_cve_ids column missing")

if "observed_cwe_ids" in df.columns:
    cwe_detects = df.filter(pl.col("observed_cwe_ids").list.len() > 0)
    print(f"Events with CWEs: {len(cwe_detects)}")
    if len(cwe_detects) > 0:
        print(cwe_detects.select(["observed_cwe_ids"]).head())
else:
    print("observed_cwe_ids column missing")
