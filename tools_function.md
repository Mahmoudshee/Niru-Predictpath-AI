# PredictPath AI: Technical System Workflow

This document details the internal logic and data flow of the **Unified Event Intelligence Pipeline** (Tools 1-6).

## 📊 Phase 1: Event Intelligence (Tool 1)
**Purpose:** Transform raw, noisy security logs into structured, AI-enriched intelligence.

*   **Ingestion:** Supports multiple formats (LANL Auth logs, CICIDS Network traffic) via dedicated classes (`LanlAuthIngestor`, `CicIdsIngestor`).
*   **Deep Enrichment:** Uses the `all-MiniLM-L6-v2` transformer model to perform **Semantic MITRE Mapping**. It compares log descriptions against a technique database to assign MITRE IDs (e.g., `T1078` for valid logins) with a confidence score.
*   **Data Quality:** Calculates a `data_quality_score` by penalizing missing fields or placeholder characters like `?`.
*   **Output:** Generates compressed **Parquet** files, allowing the rest of the system to query millions of events in milliseconds via DuckDB.

---

## 🗺️ Phase 2: Path Reconstruction (Tool 2)
**Purpose:** Reconstruct the chain of events and identify the "Blast Radius" of an attack.

*   **Session Tracking:** Groups enriched events by User and Host into logical sessions.
*   **Temporal Graph:** Builds a **Directed Temporal Graph** where nodes are events and edges represent the "Time Delta" between actions.
*   **Risk Scoring:** Calculates a `path_anomaly_score` based on:
    *   Accumulated MITRE weights (Pass-the-hash carries more weight than a standard login).
    *   **Velocity:** Detects "Machine Speed" attacks (deltas < 0.2s) vs. "Low and Slow" persistence.
    *   **Blast Radius:** Quantifies how many unique hosts were touched during the session.
*   **Prediction Vector:** Uses a probability matrix to suggest the most likely next Phase in the Cyber Kill Chain.

---

## 🔮 Phase 3: Trajectory Forecasting (Tool 3)
**Purpose:** Predict the "Future State" of a threat and estimate time-to-impact.

*   **Scenario Simulation:** Takes the prediction vector from Tool 2 and runs simulations to generate specific "Projected Scenarios."
*   **Risk Categorization:** Assigns risk levels (Critical, High, Medium) based on the predicted sequence of techniques.
*   **Reaction Windows:** Estimates the `min_seconds` and `max_seconds` remaining before the next stage of the attack is likely to occur, giving the SOC a specific "Time to Act."

---

## ⚖️ Phase 4: Adaptive Response Planning (Tool 4)
**Purpose:** Prioritize threats globally and select the safest, most effective countermeasure.

*   **Consolidated Board:** Groups overlapping sessions (e.g., a single user attacking 5 different hosts) into one "Principal" decision point.
*   **Decision Engine:** Evaluates candidate actions (Isolate User, Block IP, Revoke Token) against the threat.
*   **Strategy Rejection:** Automatically filters out actions that are too disruptive relative to the risk (e.g., it won't shut down a production server for a "Low" risk event).
*   **Justification:** Each recommendation includes a "What Happens if Ignored" explanation for the human analyst.

---

## ⚡ Phase 5: Controlled Execution (Tool 5)
**Purpose:** Execute the plan while maintaining a strict audit trail.

*   **Execution Modes:**
    *   **AUTO:** For low-risk containment (e.g., blocking a known malicious IP).
    *   **STAGED:** Held for human approval (e.g., disabling a CEO's account).
*   **Safety Checks:** Operates in a **Simulation Mode** by default unless explicitly toggled in configuration.
*   **Rollback Support:** Generates "Rollback Tokens" for every action, allowing the system to undo changes if they cause collateral damage.

---

## 🏛️ Phase 6: Governance & Learning (Tool 6)
**Purpose:** The "System Conscience" that adjusts the entire pipeline's behavior.

*   **Trust Ledger:** Records every action taken by Tool 5 into a permanent SQLite database for compliance.
*   **Learning Engine:** Implements a feedback loop.
    *   **Success Streaks:** If consecutive actions are successful, it "relaxes" thresholds (Trust Momentum ↗).
    *   **Failure Streaks:** If actions fail or are manually overridden, it "tightens" thresholds (Trust Momentum ↘), requiring more human approval for future actions.
*   **Self-Tuning:** Dynamically updates the `containment_threshold` that determines when Tools 4 and 5 can act autonomously.

---

### 🔄 The Full Loop Summary
1.  **Log** enters (Tool 1).
2.  **Path** is mapped (Tool 2).
3.  **Future** is predicted (Tool 3).
4.  **Plan** is made (Tool 4).
5.  **Action** is taken (Tool 5).
6.  **System** learns and adjusts (Tool 6).
