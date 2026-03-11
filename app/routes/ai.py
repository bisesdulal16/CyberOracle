import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.jwt_utils import get_current_user
from app.schemas.ai_schema import (
    AIQueryRequest,
    AIQueryResponse,
    ModelResult,
    PolicyResult,
)
from app.services.model_router import route_many, route_one
from app.utils.logger import log_request, secure_log

router = APIRouter()


@router.post("/query", response_model=AIQueryResponse)
async def ai_query(
    payload: AIQueryRequest,
    user_payload: dict = Depends(get_current_user),
):
    request_id = uuid4()
    t0 = time.perf_counter()

    # Policy stub
    size_ok = len(payload.prompt) <= 8000
    policy = PolicyResult(rbac="pass", size="pass" if size_ok else "fail")

    if not size_ok:
        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested="N/A",
            model_used="N/A",
            latency_ms=0,
            policy=policy,
            status_code=413,
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "request_id": str(request_id),
                "policy": policy.model_dump(),
            },
        )

    try:
        if payload.models:
            raw_results = await route_many(
                payload.prompt,
                payload.models,
                user_payload,
            )
            results = [
                ModelResult(
                    answer=r["answer"],
                    model_used=r["model_used"],
                )
                for r in raw_results
            ]

            latency_ms = int((time.perf_counter() - t0) * 1000)

            await _log_ai(
                request_id=request_id,
                user_payload=user_payload,
                model_requested=",".join(payload.models),
                model_used="multi",
                latency_ms=latency_ms,
                policy=policy,
                status_code=200,
            )

            return AIQueryResponse(
                request_id=request_id,
                policy=policy,
                answer=results[0].answer if results else "",
                model_used=results[0].model_used if results else "",
                results=results,
            )

        result = await route_one(
            payload.prompt,
            payload.model,
            user_payload,
        )

        latency_ms = int((time.perf_counter() - t0) * 1000)

        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested=payload.model,
            model_used=result["model_used"],
            latency_ms=latency_ms,
            policy=policy,
            status_code=200,
        )

        return AIQueryResponse(
            request_id=request_id,
            policy=policy,
            answer=result["answer"],
            model_used=result["model_used"],
            results=None,
        )

    except ValueError as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested="error",
            model_used="N/A",
            latency_ms=latency_ms,
            policy=policy,
            status_code=400,
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        await _log_ai(
            request_id=request_id,
            user_payload=user_payload,
            model_requested="error",
            model_used="N/A",
            latency_ms=latency_ms,
            policy=policy,
            status_code=500,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def _log_ai(
    request_id,
    user_payload,
    model_requested,
    model_used,
    latency_ms,
    policy,
    status_code: int,
):
    user_id = user_payload.get("user_id") or user_payload.get("id") or "unknown"

    secure_log(
        f"AI_QUERY request_id={request_id} user_id={user_id} "
        f"model_requested={model_requested} model_used={model_used} "
        f"latency_ms={latency_ms} status_code={status_code} "
        f"policy={policy.model_dump()}"
    )

    await log_request(
        endpoint="/ai/query",
        method="POST",
        status_code=status_code,
        message=(
            f"request_id={request_id} user_id={user_id} "
            f"model_requested={model_requested} model_used={model_used} "
            f"latency_ms={latency_ms} policy={policy.model_dump()}"
        ),
    )
