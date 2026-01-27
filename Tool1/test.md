.\.venv\Scripts\Activate.ps1
1. Clean Start
First, clear the output directories to ensure a fresh test run.

powershell
rm -r data/output, data/dlq
mkdir data/output, data/dlq
(Note: standard PowerShell commands may differ slightly, but simply deleting these folders is the goal).

2. Ingest the Data
Run the ingestion on the 
lanl_small.txt
 sample.

powershell
python -m src.main ingest data/samples/lanl_small.txt --type lanl
Expected Outcome:

Valid events written: 4
Rejected events: 0
Output directory: data/output/lanl/
3. Verification (Querying)
We verified the data actually landed in DuckDB/Parquet with the correct schema and enrichment scores.

powershell
python -m src.main query "SELECT event_id, user, source_host, event_type, mitre_technique, confidence_score, data_quality_score FROM 'data/output/**/*.parquet' ORDER BY event_id;"
Key checks:

confidence_score should be between 0.0 and 1.0.
data_quality_score should be lower for the authentication failure event (line 4 in your file).
mitre_technique should be populated (e.g., T1078 or T1110).
4. Test Rejection (DLQ)
We append garbage data to test if the "Dead Letter Queue" works.

powershell
Add-Content -Path data/samples/lanl_small.txt -Value "THIS_IS_GARBAGE"
python -m src.main ingest data/samples/lanl_small.txt --type lanl
Then query the DLQ:

powershell
python -m src.main query "SELECT rejection_reason, raw_source FROM 'data/dlq/**/*.parquet';"
5. Deterministic Replay
We ran the ingestion twice and hashed the output files to ensure that running the same data always produces the exact same Parquet files (same bytes).

powershell
Get-FileHash data/output/**/*.parquet
Would you like me to execute Step 2 (Ingestion) now to confirm the current state of the codebase?

how do i go into the env when i open terminal


Thought for 1s




To activate the virtual environment in your terminal, run the following command from the root of your project (Tool1 folder):

For PowerShell (default in VS Code):

powershell
.\.venv\Scripts\Activate.ps1
For Command Prompt (cmd):

cmd
.venv\Scripts\activate.bat
Once activated, you should see (.venv) appear at the start of your command prompt line.

If you get a "running scripts is disabled" error in PowerShell, you can temporarily allow it by running:

powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
Then run the activate command again.


# switch to Tool 2 directory
cd 'C:\Users\cisco\Documents\NiRu predictpath tools\Tool2'

# Run the engine
# Note: Ensure the path matches where Tool 1 saved the data. 
# Since we just ran Tool 1, there should be a fresh file in Tool1\data\output\...\
python -m src.main "..\Tool1\data\output\**\*.parquet" --threshold 0.0