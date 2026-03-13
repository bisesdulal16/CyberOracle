# 🧩 CyberOracle — AI Gateway Integration Report

**Contributor:** Bishesh Dulal  
**Role:** Backend / AI Gateway / Security Integration  
**Period:** March 2026

---

## 🎯 Objectives
The **CyberOracle AI Gateway** is designed to serve as a secure intermediary between clients and diverse AI models. It enforces a "Security-First" approach by integrating:
* **Identity Management:** JWT-based authentication.
* **Data Loss Prevention (DLP):** Bi-directional scanning (Input/Output).
* **Orchestration:** Multi-model routing and simultaneous execution.
* **Observability:** Comprehensive PostgreSQL logging and latency tracking.

---

## ⚙️ System Architecture
The gateway operates as a linear pipeline with security "gates" that must be passed before a prompt reaches the LLM provider.



### 1. Request Flow & Security Layers
1.  **Authentication:** JWT verification via FastAPI `Depends(get_current_user)`.
2.  **Validation:** Pydantic schemas enforce strict prompt/model parameters.
3.  **Inbound DLP:** Presidio scans for PII/sensitive data. 
    * *Actions:* `ALLOW`, `REDACT`, or `BLOCK`.
4.  **Routing & Execution:** The Model Router directs the sanitized prompt to specified adapters (e.g., `ollama:llama3`).
5.  **Outbound DLP:** Model responses are scanned for sensitive leaks before reaching the user.
6.  **Telemetry:** Metadata is committed to PostgreSQL for audit trails.

---

## 🧠 Tasks Completed

| Task | Tools | Status |
| :--- | :--- | :--- |
| Secure `/ai/query` API Implementation | FastAPI | ✅ |
| JWT Security Integration | FastAPI Security | ✅ |
| Adapter-based Model Routing | Python | ✅ |
| Multi-Model Prompt Execution | Concurrent Python | ✅ |
| PII Scanning (In/Out) | Presidio DLP | ✅ |
| Structured SQL Logging | PostgreSQL | ✅ |
| Request ID & Latency Tracing | Python / Middleware | ✅ |
| Automated Logic Verification | Pytest | ✅ |

---

## 📦 Deliverables

* **Secure Endpoint:** A hardened `/ai/query` gateway.
* **Model Router:** Flexible adapter layer supporting `ollama` prefixes.
* **Security Suite:** Real-time redaction and blocking logic.
* **Audit Log:** A `logs` table in PostgreSQL capturing risk scores and latency.

---

## 📊 Technical Implementation Details

### Multi-Model Request Example
The gateway handles array-based model selection to compare outputs in a single round-trip.

**Request:**
```json
{
  "prompt": "Explain zero-trust security.",
  "models": ["ollama:llama3", "ollama:mistral"]
}

**Response:**
```json
{
  "results": [
    { "model_used": "ollama:llama3", "answer": "..." },
    { "model_used": "ollama:mistral", "answer": "..." }
  ]
}