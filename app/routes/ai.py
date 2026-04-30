# app/routes/ai.py

import os
import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services import dlp_engine
from app.services.dlp_engine import DlpFinding, PolicyDecision, _severity_for_entity
from app.utils.logger import log_request, mask_sensitive

# RBAC permission enforcement
from app.auth.rbac import require_permission

from app.middleware.api_key_auth import verify_api_key

router = APIRouter()

# ---------------------------------------------------------------------------
# Default Ollama model — used when the client selects the bare "ollama" option
# ---------------------------------------------------------------------------
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


# ---------------------------------------------------------------------------
# Available models catalogue — only expose providers whose key is configured
# ---------------------------------------------------------------------------
def _available_models() -> List[dict]:
    models = [
        {
            "id": f"ollama:{OLLAMA_MODEL}",
            "label": f"Ollama ({OLLAMA_MODEL})",
            "provider": "ollama",
        }
    ]
    if os.getenv("OPENAI_API_KEY"):
        models += [
            {"id": "openai:gpt-4o", "label": "GPT-4o", "provider": "openai"},
            {"id": "openai:gpt-4o-mini", "label": "GPT-4o Mini", "provider": "openai"},
            {
                "id": "openai:gpt-3.5-turbo",
                "label": "GPT-3.5 Turbo",
                "provider": "openai",
            },
        ]
    if os.getenv("ANTHROPIC_API_KEY"):
        models += [
            {
                "id": "anthropic:claude-3-5-haiku-20241022",
                "label": "Claude 3.5 Haiku",
                "provider": "anthropic",
            },
            {
                "id": "anthropic:claude-3-5-sonnet-20241022",
                "label": "Claude 3.5 Sonnet",
                "provider": "anthropic",
            },
        ]
    if os.getenv("GOOGLE_API_KEY"):
        models += [
            {
                "id": "gemini:gemini-2.0-flash",
                "label": "Gemini 2.0 Flash",
                "provider": "gemini",
            },
            {
                "id": "gemini:gemini-2.0-flash-lite",
                "label": "Gemini 2.0 Flash Lite",
                "provider": "gemini",
            },
        ]
    if os.getenv("GROQ_API_KEY"):
        models += [
            {
                "id": "groq:llama-3.3-70b-versatile",
                "label": "Llama 3.3 70B",
                "provider": "groq",
            },
            {
                "id": "groq:llama-3.1-8b-instant",
                "label": "Llama 3.1 8B (fast)",
                "provider": "groq",
            },
            {
                "id": "groq:meta-llama/llama-4-scout-17b-16e-instruct",
                "label": "Llama 4 Scout 17B",
                "provider": "groq",
            },
            {
                "id": "groq:qwen/qwen3-32b",
                "label": "Qwen3 32B",
                "provider": "groq",
            },
        ]
    return models


class AIQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    # Full model identifier, e.g. "ollama:llama3.2:1b", "openai:gpt-4o"
    # Legacy bare "ollama" value is accepted and resolved to the env default.
    model: str = Field(default="ollama")


class AIQueryResponse(BaseModel):
    request_id: str
    model: str
    output: dict
    security: dict
    meta: dict


@router.get("/ai/models")
async def list_models():
    """Return the models available in this deployment."""
    return {"models": _available_models()}


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
    Secure AI Gateway endpoint — supports Ollama, OpenAI, Anthropic, Gemini.
    Flow:
      1) Resolve model identifier
      2) DLP scan input
      3) Block early if needed
      4) Route to selected model adapter
      5) DLP scan output
      6) Redact/block output if needed
      7) Log masked event
      8) Return response with security metadata
    """

    start = time.time()
    request_id = str(uuid.uuid4())
    client_ip = request.client.host if request.client else None

    # ------------------------------------------------------------------
    # 1) RESOLVE MODEL
    # Legacy bare "ollama" → resolved to env-configured default with prefix
    # ------------------------------------------------------------------
    if req.model == "ollama" or not req.model:
        selected_model = f"ollama:{OLLAMA_MODEL}"
    else:
        selected_model = req.model

    # ------------------------------------------------------------------
    # 2) INPUT DLP
    # ------------------------------------------------------------------
    input_redacted_text, input_findings = dlp_engine.scan_text(req.prompt)
    input_decision = dlp_engine.decide(input_findings)

    # Merge any entities caught by DLPFilterMiddleware (which redacted before we saw them)
    middleware_entities = getattr(request.state, "dlp_middleware_entities", set())
    seen_types = {f.type for f in input_findings}
    for entity_type in middleware_entities:
        if entity_type not in seen_types:
            input_findings.append(
                DlpFinding(
                    type=entity_type,
                    count=1,
                    severity=_severity_for_entity(entity_type),
                )
            )
    if middleware_entities:
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
                    "model": selected_model,
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
            model=selected_model,
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
    # 3) MODEL CALL via router
    # ------------------------------------------------------------------
    try:
        result = await model_router.route_one(prompt_for_model, selected_model, _user)
        raw_output = result["answer"]
        model_used = result["model_used"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
                    "model": selected_model,
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
    # 4) OUTPUT DLP
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
    # 5) LOG
    # ------------------------------------------------------------------
    log_payload = {
        "event": "ai_query",
        "request_id": request_id,
        "model": model_used,
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
    # 6) RESPONSE
    # ------------------------------------------------------------------
    return AIQueryResponse(
        request_id=request_id,
        model=model_used,
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
