# 🛡️ CyberOracle — Week 5 Progress Report

**Contributor:** Pradip Sapkota  
**Role:** DLP Engineering / Middleware Integration  
**Period:** Nov 25 – Nov 29, 2025  

---

## 🎯 Objectives

Extend the CyberOracle DLP pipeline into a unified **"DLP v2"** workflow by integrating the regex engine, Presidio engine, and FastAPI middleware. Validate end-to-end detection, sanitization, and alerting behavior across both API routes and middleware-protected ingestion endpoints.

---

## 🧠 Work Completed

### **Integration**

| Task | Status |
|------|--------|
| Added `LogIngest` Pydantic schema for JSON validation | ✅ |
| Updated `/logs/ingest` to accept structured input | ✅ |
| Verified DLP middleware intercepts and sanitizes request bodies | ✅ |
| Ensured compatibility with `mask_sensitive` and database logger | ✅ |

### **DLP v2 Pipeline**

**Regex Detection via `/api/scan`:**
- SSNs → `<GENERIC_SSN>`
- Emails → `<EMAIL_ADDRESS>`
- API keys → `<GENERIC_API_KEY>`

**Presidio Detection:**
- ✅ Tested SSN + Email combinations
- ✅ Confirmed high-confidence entity recognition
- ✅ Verified anonymized output formatting

### **Middleware Behavior**

- ✅ Middleware correctly intercepted and sanitized payloads before ingestion
- ✅ Sanitized payload forwarded to route, then masked again before storage
- ✅ Ingestion endpoint logs masked content only (OWASP-ASVS 9.1 & 9.2 compliant)

### **Alerting**

- ✅ Middleware-initiated Presidio detections triggered Discord alerts via `alert_manager`
- ✅ Validated alert format: severity, timestamps, and source context
- ✅ Ensured duplicate alerts per request were avoided

---

## 🧪 Tests and Verification

### **1️⃣ `/logs/ingest` Ingestion Test**

**Request body:**
```json
{
  "message": "User John Doe with SSN 219-09-9999 logged in"
}
```

**Observed behavior:**
- Middleware sanitized SSN to `<GENERIC_SSN>`
- Endpoint stored masked version in the database
- Response returned:
```json
{
  "message": "Log stored successfully"
}
```

**Result:** ✅ Successful end-to-end ingestion with DLP enforcement.

---

### **2️⃣ `/api/scan` Comprehensive DLP Test**

**Input:**
```json
{
  "message": "SSN 219-09-9999, email john@gmail.com, key=ABC123456789098765432"
}
```

**Expected:**
- SSN → `<GENERIC_SSN>`
- Email → `<EMAIL_ADDRESS>`
- API key → `<GENERIC_API_KEY>`

**Swagger result:**
- ✅ Redacted output returned correctly
- ✅ No Presidio errors
- ✅ Middleware bypassed (direct API access)

**Result:** ✅ Regex + Presidio detection functioning as intended.

---

### **3️⃣ Validation and Error Handling**

**Tested malformed JSON inputs to ensure:**
- ✅ FastAPI returned proper 422 validation errors
- ✅ Logs weren't stored when schema validation failed
- ✅ Middleware did not trigger alerts for invalid inputs

---

## 📦 Deliverables Produced

| Deliverable | Description |
|-------------|-------------|
| **Updated `/logs/ingest` endpoint** | Schema-based input validation + middleware compatibility |
| **DLP v2 unified flow** | Regex + Presidio + middleware all functioning together |
| **End-to-end screenshots** | `/api/scan` and `/logs/ingest` test results validated in Swagger |
| **Sanitization + Alerting tests** | Realistic payloads executed through both pipelines |
| **Logging verification** | Masked logs stored in database via SQLAlchemy |

---

## 📈 Progress

**Overall Project Progress:** **33%**

Week 5 DLP integration brings the project to 33% cumulative completion. The platform now supports unified detection, consistent sanitization, and complete request-level enforcement across all ingestion paths.

---

## 🚀 Next Steps (Week 6)

- [ ] Improve Presidio recognizer scoring for borderline entity patterns
- [ ] Expand red-team dataset for accuracy benchmarking
- [ ] Generate precision/recall metrics comparing Regex vs Presidio
- [ ] Add support for contextual detection (e.g., "my ssn is …")
- [ ] Begin drafting DLP v2 evaluation documentation for the final report

---