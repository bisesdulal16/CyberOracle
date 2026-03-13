import time
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

# JWT authentication dependency
from app.auth.jwt_utils import get_current_user

# Request/response schemas for the AI endpoint
from app.schemas.ai_schema import (
    AIQueryRequest,
    AIQueryResponse,
    ModelResult,
    PolicyResult,
)

# DLP engine used for scanning prompts and model outputs
from app.services import dlp_engine
from app.services.dlp_engine import PolicyDecision

# Model routing layer (handles adapter dispatching)
from app.services.model_router import route_many, route_one

# Logging utilities
from app.utils.logger import log_request, secure_log

# RBAC permission enforcement
from app.auth.rbac import require_permission

router = APIRouter()


# Main AI query endpoint
# Handles:
# - authentication
# - input validation
# - DLP scanning
# - model routing
# - output filtering
# - structured logging
@router.post("/query", response_model=AIQueryResponse)
async def ai_query(
    payload: AIQueryRequest,
    user_payload: dict = Depends(get_current_user),
):
    # Generate unique request ID for traceability
    request_id = uuid4()

    # Start latency timer
    t0 = time.perf_counter()

    # Basic request size policy check
    size_ok = len(payload.prompt) <= 8000

    # Policy tracking object
    policy = PolicyResult(rbac="pass", size="pass" if size_ok else "fail")

    # Reject request if prompt exceeds allowed size
    if not size_ok:
        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested="N/A",
            model_used="N/A",
            latency_ms=0,
            policy=policy,
            status_code=413,
            risk_score=None,
            rules_triggered=[],
            blocked=True,
            redacted=False,
        )

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "request_id": str(request_id),
                "policy": policy.model_dump(),
            },
        )

    # ------------------------------
    # INPUT DLP SCAN
    # ------------------------------

    # Scan prompt for sensitive data
    input_redacted_text, input_findings = dlp_engine.scan_text(payload.prompt)

    # Decide policy based on findings
    input_decision = dlp_engine.decide(input_findings)

    # Extract triggered rule names
    input_rules = [f.type for f in input_findings]

    # Risk score assigned by DLP
    input_risk = input_decision.risk_score

    # If input violates policy, block request immediately
    if input_decision.decision == PolicyDecision.BLOCK:
        latency_ms = int((time.perf_counter() - t0) * 1000)

        requested_models = ",".join(payload.models) if payload.models else payload.model

        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested=requested_models,
            model_used="N/A",
            latency_ms=latency_ms,
            policy=policy,
            status_code=200,
            risk_score=input_risk,
            rules_triggered=input_rules,
            blocked=True,
            redacted=False,
        )

        return AIQueryResponse(
            request_id=request_id,
            policy=policy,
            answer="Request blocked by DLP policy.",
            model_used="blocked",
            results=None,
        )

    try:

        # ===============================
        # MULTI-MODEL EXECUTION PATH
        # ===============================

        if payload.models:

            # Send prompt to multiple models
            raw_results = await route_many(
                input_redacted_text,
                payload.models,
                user_payload,
            )

            results: List[ModelResult] = []
            blocked_any = False
            redacted_any = False

            all_rules = list(input_rules)
            combined_risk = input_risk

            # Process each model response independently
            for item in raw_results:

                # Scan model output for sensitive data
                output_redacted_text, output_findings = dlp_engine.scan_text(
                    item["answer"]
                )

                output_decision = dlp_engine.decide(output_findings)

                output_rules = [f.type for f in output_findings]

                all_rules.extend(output_rules)

                # Track highest risk score
                combined_risk = max(combined_risk, output_decision.risk_score)

                final_answer = item["answer"]

                # Output policy enforcement
                if output_decision.decision == PolicyDecision.BLOCK:
                    final_answer = "Response blocked by DLP policy."
                    blocked_any = True

                elif output_decision.decision == PolicyDecision.REDACT:
                    final_answer, _ = dlp_engine.redact_text(
                        output_redacted_text,
                        output_findings,
                    )
                    redacted_any = True

                results.append(
                    ModelResult(
                        answer=final_answer,
                        model_used=item["model_used"],
                    )
                )

            latency_ms = int((time.perf_counter() - t0) * 1000)

            # Log the full multi-model request
            await _log_ai(
                request_id=request_id,
                user_payload=user_payload,
                model_requested=",".join(payload.models),
                model_used="multi",
                latency_ms=latency_ms,
                policy=policy,
                status_code=200,
                risk_score=combined_risk,
                rules_triggered=sorted(set(all_rules)),
                blocked=blocked_any,
                redacted=redacted_any,
            )

            return AIQueryResponse(
                request_id=request_id,
                policy=policy,
                answer=results[0].answer if results else "",
                model_used=results[0].model_used if results else "",
                results=results,
            )

        # ===============================
        # SINGLE MODEL EXECUTION PATH
        # ===============================

        result = await route_one(
            input_redacted_text,
            payload.model,
            user_payload,
        )

        # Scan model output for sensitive data
        output_redacted_text, output_findings = dlp_engine.scan_text(result["answer"])

        output_decision = dlp_engine.decide(output_findings)

        output_rules = [f.type for f in output_findings]

        combined_risk = max(input_risk, output_decision.risk_score)

        all_rules = sorted(set(input_rules + output_rules))

        final_answer = result["answer"]

        blocked = False
        redacted = False

        # Apply output policy enforcement
        if output_decision.decision == PolicyDecision.BLOCK:
            final_answer = "Response blocked by DLP policy."
            blocked = True

        elif output_decision.decision == PolicyDecision.REDACT:
            final_answer, _ = dlp_engine.redact_text(
                output_redacted_text,
                output_findings,
            )
            redacted = True

        latency_ms = int((time.perf_counter() - t0) * 1000)

        # Log request metadata
        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested=payload.model,
            model_used=result["model_used"],
            latency_ms=latency_ms,
            policy=policy,
            status_code=200,
            risk_score=combined_risk,
            rules_triggered=all_rules,
            blocked=blocked,
            redacted=redacted,
        )

        return AIQueryResponse(
            request_id=request_id,
            policy=policy,
            answer=final_answer,
            model_used=result["model_used"],
            results=None,
        )

    # ------------------------------
    # ROUTER VALIDATION ERRORS
    # ------------------------------

    except ValueError as exc:

        latency_ms = int((time.perf_counter() - t0) * 1000)

        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested="error",
            model_used="N/A",
            latency_ms=latency_ms,
            policy=policy,
            status_code=400,
            risk_score=input_risk,
            rules_triggered=input_rules,
            blocked=False,
            redacted=False,
        )

        raise HTTPException(status_code=400, detail=str(exc))

    # ------------------------------
    # INTERNAL SERVER ERRORS
    # ------------------------------

    except Exception as exc:

        latency_ms = int((time.perf_counter() - t0) * 1000)

        secure_log(f"AI route exception: {repr(exc)}")

        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested="error",
            model_used="N/A",
            latency_ms=latency_ms,
            policy=policy,
            status_code=500,
            risk_score=input_risk,
            rules_triggered=input_rules,
            blocked=False,
            redacted=False,
        )

        raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------------------
# Internal logging helper
# ------------------------------------------
# Centralized logging function used by the AI route
# Stores structured logs and sends sanitized logs
# to secure logging output.
async def _log_ai(
    request_id,
    user_payload,
    model_requested,
    model_used,
    latency_ms,
    policy,
    status_code: int,
    risk_score=None,
    rules_triggered=None,
    blocked: bool = False,
    redacted: bool = False,
):

    user_id = user_payload.get("user_id") or user_payload.get("id") or "unknown"

    rules_triggered = rules_triggered or []

    secure_log(
        f"AI_QUERY request_id={request_id} user_id={user_id} "
        f"model_requested={model_requested} model_used={model_used} "
        f"latency_ms={latency_ms} status_code={status_code} "
        f"risk_score={risk_score} rules_triggered={rules_triggered} "
        f"blocked={blocked} redacted={redacted} "
        f"policy={policy.model_dump()}"
    )

    await log_request(
        endpoint="/ai/query",
        method="POST",
        status_code=status_code,
        message=(
            f"request_id={request_id} user_id={user_id} "
            f"model_requested={model_requested} model_used={model_used} "
            f"latency_ms={latency_ms} risk_score={risk_score} "
            f"rules_triggered={rules_triggered} blocked={blocked} "
            f"redacted={redacted} policy={policy.model_dump()}"
        ),
    )
