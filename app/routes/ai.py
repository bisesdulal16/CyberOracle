# app/routes/ai.py

import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.auth.rbac import require_roles
from app.services.ollama_client import OllamaClient
from app.services import dlp_engine
from app.services.dlp_engine import PolicyDecision
from app.utils.logger import log_request, mask_sensitive

router = APIRouter()


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


@router.post("/ai/query", response_model=AIQueryResponse)
async def ai_query(
    req: AIQueryRequest,
    request: Request,
    _user: dict = Depends(require_roles("admin", "developer")),
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

    # ✅ MVP: Force Ollama model tag (avoid client sending "openai" etc.)
    model = "llama3:latest"

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

        # log failure too (masked)
        masked_log = mask_sensitive(
            str(
                {
                    "event": "ai_query_model_error",
                    "request_id": request_id,
                    "model": model,
                    "error": repr(e),
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

        raise HTTPException(status_code=502, detail=repr(e))

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

    # Check if DLP was detected in middleware
    dlp_detected = getattr(request.state, 'dlp_detected', False)
    dlp_entities = getattr(request.state, 'dlp_entities', [])
    dlp_policy_decision = getattr(request.state, 'dlp_policy_decision', 'allow')
    dlp_risk_score = getattr(request.state, 'dlp_risk_score', 0.0)
    dlp_severity = getattr(request.state, 'dlp_severity', 'low')

    # Use middleware DLP metadata if available
    if dlp_detected:
        # Update the logging values to reflect middleware DLP detection
        policy_decision = dlp_policy_decision
        risk_score = dlp_risk_score
        rules_triggered = dlp_entities
        redacted = True
        severity = dlp_severity
    else:
        policy_decision = output_decision.decision.value
        risk_score = combined_risk
        rules_triggered = all_rules
        redacted = redacted_flag
        severity = "high" if combined_risk >= 0.7 else "medium" if combined_risk >= 0.3 else "low"

    log_payload = {
        "event": "ai_query",
        "request_id": request_id,
        "model": model,
        "input_preview": req.prompt[:200],
        "output_preview": raw_output[:200],
        "policy_decision": policy_decision,
        "risk_score": risk_score,
        "rules_triggered": rules_triggered,
        "redactions": redactions_meta,
        "redacted": redacted,
        "blocked": blocked_flag,
        "latency_ms": latency_ms,
        "client_ip": client_ip,
    }

    masked_log = mask_sensitive(str(log_payload))
    await log_request(
        endpoint="/ai/query",
        method="POST",
        status_code=200,
        message=masked_log,
        event_type="ai_query",
        severity=severity,
        risk_score=risk_score,
        source="ai_route",
        policy_decision=policy_decision,
    )

    # ------------------------------------------------------------------
    # 5) RESPONSE
    # ------------------------------------------------------------------

    # Use middleware DLP metadata if available for the response
    if dlp_detected:
        policy_decision = dlp_policy_decision
        risk_score = dlp_risk_score
        rules_triggered = dlp_entities
        redacted = True
        blocked = blocked_flag
    else:
        policy_decision = output_decision.decision.value
        risk_score = combined_risk
        rules_triggered = all_rules
        redacted = redacted_flag
        blocked = blocked_flag

    return AIQueryResponse(
        request_id=request_id,
        model=model,
        output={"text": final_text, "redacted": redacted, "blocked": blocked},
        security={
            "policy_decision": policy_decision,
            "risk_score": risk_score,
            "rules_triggered": rules_triggered,
            "redactions": redactions_meta,
            "blocked_reason": blocked_reason,
            "phase": "output",
        },
        meta={"latency_ms": latency_ms},
    )
