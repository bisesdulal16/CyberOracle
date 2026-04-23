# app/routes/ai.py

import os
import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services.ollama_client import OllamaClient
from app.services import dlp_engine
from app.services.dlp_engine import PolicyDecision
from app.utils.logger import log_request, mask_sensitive

# RBAC permission enforcement
from app.auth.rbac import require_permission

from app.middleware.api_key_auth import verify_api_key

router = APIRouter()

# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------
# Override via OLLAMA_MODEL env var, e.g:
#   OLLAMA_MODEL=llama3:latest        (full model, GPU recommended)
#   OLLAMA_MODEL=llama3.2:1b          (fast, CPU-friendly)
#   OLLAMA_MODEL=llama3.2:3b          (balanced)
# Defaults to llama3.2:1b for CPU performance when no GPU is available.
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


class AIQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    # Keep field for backward compat, but we will ignore it for MVP
    model: str = Field(default="ollama")


class AIQueryResponse(BaseModel):
    request_id: str
    model: str
    output: dict
    security: dict
    meta: dict


@router.options("/ai/query")
async def ai_query_options():
    return Response(status_code=200)


@router.options("/ai/query/")
async def ai_query_options_slash():
    return Response(status_code=200)


# RBAC: only users with test_api_endpoints permission may access the AI gateway
@router.post("/ai/query", response_model=AIQueryResponse)
async def ai_query(
    req: AIQueryRequest,
    request: Request,
    _user: dict = Depends(require_permission("test_api_endpoints")),
):
    """
    Secure AI Gateway endpoint (MVP: Ollama-only)
    Flow:
      1) DLP scan input
      2) Block early if needed
      3) Call Ollama
      4) DLP scan output
      5) redact/block output if needed
      6) log masked event
      7) return response with security metadata
    """

    start = time.time()
    request_id = str(uuid.uuid4())
    client_ip = request.client.host if request.client else None

    # Use env-configured model (defaults to llama3.2:1b for CPU performance)
    model = OLLAMA_MODEL

    # ------------------------------------------------------------------
    # 1) INPUT DLP
    # ------------------------------------------------------------------
    input_redacted_text, input_findings = dlp_engine.scan_text(req.prompt)
    input_decision = dlp_engine.decide(input_findings)

    input_rules = [f.type for f in input_findings]
    input_risk = input_decision.risk_score

    prompt_for_model = input_redacted_text  # model never sees raw secrets if detected

    # BLOCK on input
    if input_decision.decision == PolicyDecision.BLOCK:
        latency_ms = int((time.time() - start) * 1000)

        masked_log = mask_sensitive(
            str(
                {
                    "event": "ai_query_blocked_input",
                    "request_id": request_id,
                    "model": model,
                    "risk_score": input_risk,
                    "rules_triggered": input_rules,
                    "client_ip": client_ip,
                }
            )
        )

        await log_request(
            endpoint="/ai/query",
            method="POST",
            status_code=200,
            message=masked_log,
            event_type="ai_query_blocked",
            severity="high",
            risk_score=input_risk,
            source="ai_route",
            policy_decision="block",
        )

        return AIQueryResponse(
            request_id=request_id,
            model=model,
            output={
                "text": "Request blocked by DLP policy.",
                "redacted": False,
                "blocked": True,
            },
            security={
                "policy_decision": "block",
                "risk_score": input_risk,
                "rules_triggered": input_rules,
                "redactions": [],
                "blocked_reason": "Sensitive data detected in input.",
                "phase": "input",
            },
            meta={"latency_ms": latency_ms},
        )

    # ------------------------------------------------------------------
    # 2) MODEL CALL
    # ------------------------------------------------------------------
    client = OllamaClient()

    try:
        raw_output = await client.generate(model, prompt_for_model)
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)

        # Log full error detail server-side only — never expose to client
        # repr(e) may contain connection strings or internal hostnames
        import logging as _logging
        _logging.getLogger("cyberoracle").error(
            f"Model call failed [{request_id}]: {type(e).__name__}: {e}"
        )

        masked_log = mask_sensitive(
            str(
                {
                    "event": "ai_query_model_error",
                    "request_id": request_id,
                    "model": model,
                    # Log exception type only, not full repr
                    "error_type": type(e).__name__,
                    "client_ip": client_ip,
                }
            )
        )
        await log_request(
            endpoint="/ai/query",
            method="POST",
            status_code=502,
            message=masked_log,
            event_type="ai_query_model_error",
            severity="high",
            source="ai_route",
        )

        # Return generic message — never expose repr(e) to client
        raise HTTPException(
            status_code=502,
            detail="AI model is currently unavailable. Please try again.",
        )

    # ------------------------------------------------------------------
    # 3) OUTPUT DLP (Output Filter)
    # ------------------------------------------------------------------
    output_redacted_text, output_findings = dlp_engine.scan_text(raw_output)
    output_decision = dlp_engine.decide(output_findings)

    output_rules = [f.type for f in output_findings]
    output_risk = output_decision.risk_score

    combined_risk = max(input_risk, output_risk)
    all_rules: List[str] = sorted(set(input_rules + output_rules))

    redactions_meta: List[dict] = []
    final_text = raw_output
    redacted_flag = False
    blocked_flag = False
    blocked_reason = None

    if output_decision.decision == PolicyDecision.BLOCK:
        blocked_flag = True
        final_text = "Response blocked by DLP policy."
        blocked_reason = "Sensitive data detected in model output."
    elif output_decision.decision == PolicyDecision.REDACT:
        final_text, redactions_meta = dlp_engine.redact_text(
            output_redacted_text, output_findings
        )
        redacted_flag = True

    latency_ms = int((time.time() - start) * 1000)

    # ------------------------------------------------------------------
    # 4) LOG MASKED EVENT
    # ------------------------------------------------------------------
    log_payload = {
        "event": "ai_query",
        "request_id": request_id,
        "model": model,
        "input_preview": input_redacted_text[:200],
        "output_preview": raw_output[:200],
        "policy_decision": output_decision.decision.value,
        "risk_score": combined_risk,
        "rules_triggered": all_rules,
        "redactions": redactions_meta,
        "redacted": redacted_flag,
        "blocked": blocked_flag,
        "latency_ms": latency_ms,
        "client_ip": client_ip,
    }

    _sev = (
        "high" if combined_risk >= 0.7 else "medium" if combined_risk >= 0.3 else "low"
    )

    masked_log = mask_sensitive(str(log_payload))
    await log_request(
        endpoint="/ai/query",
        method="POST",
        status_code=200,
        message=masked_log,
        event_type="ai_query",
        severity=_sev,
        risk_score=combined_risk,
        source="ai_route",
        policy_decision=output_decision.decision.value,
    )

    # ------------------------------------------------------------------
    # 5) RESPONSE
    # ------------------------------------------------------------------
    return AIQueryResponse(
        request_id=request_id,
        model=model,
        output={"text": final_text, "redacted": redacted_flag, "blocked": blocked_flag},
        security={
            "policy_decision": output_decision.decision.value,
            "risk_score": combined_risk,
            "rules_triggered": all_rules,
            "redactions": redactions_meta,
            "blocked_reason": blocked_reason,
            "phase": "output",
        },
        meta={"latency_ms": latency_ms},
    )


@router.post("/ai/query/apikey", response_model=AIQueryResponse)
async def ai_query_apikey(
    req: AIQueryRequest,
    request: Request,
    _user: dict = Depends(verify_api_key),
):
    """
    AI Gateway endpoint authenticated via X-API-Key header.
    Identical DLP pipeline to /ai/query but for machine-to-machine access.
    OWASP API2: Separate endpoint makes API key usage explicit and auditable.
    """
    return await ai_query(req, request, _user)
