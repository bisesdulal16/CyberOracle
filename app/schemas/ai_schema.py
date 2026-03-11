# app/schemas/ai_schema.py

from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

# Decision type used for policy evaluation results
# "pass" = policy satisfied
# "fail" = policy violation detected
Decision = Literal["pass", "fail"]

# Default model used when client does not specify a model
DEFAULT_MODEL = "ollama:llama3"


class AIQueryRequest(BaseModel):
    """
    Request schema for the /ai/query endpoint.

    Supports two execution modes:
    1) Single-model execution using 'model'
    2) Multi-model execution using 'models'

    If neither is provided, the system defaults to DEFAULT_MODEL.
    """

    # User prompt to send to the AI model(s)
    prompt: str = Field(..., min_length=1, max_length=8000)

    # Optional single model name (e.g., "ollama:llama3")
    model: Optional[str] = None

    # Optional list of models for multi-model execution
    models: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_model_choice(self):
        """
        Ensures request structure is valid.

        Rules:
        - Client cannot send both 'model' and 'models'
        - 'models' must contain at least one model if provided
        - If neither is provided, use the default model
        """

        # Prevent ambiguous request
        if self.model and self.models:
            raise ValueError("Provide either 'model' or 'models', not both.")

        # Prevent empty multi-model list
        if self.models is not None and len(self.models) == 0:
            raise ValueError("'models' must contain at least 1 model.")

        # Automatically assign default model if none provided
        if not self.model and not self.models:
            self.model = DEFAULT_MODEL

        return self


class PolicyResult(BaseModel):
    """
    Security policy evaluation results.

    Used to communicate whether the request passed
    basic gateway checks such as:
    - RBAC authorization
    - prompt size validation
    """

    rbac: Decision
    size: Decision


class ModelResult(BaseModel):
    """
    Result structure for a single model execution.

    Used primarily when the request includes multiple models.
    Each model returns its own result entry.
    """

    answer: str
    model_used: str


class AIQueryResponse(BaseModel):
    """
    Response schema returned by the AI gateway.

    Supports two response modes:

    Single-model:
        answer
        model_used

    Multi-model:
        results[] (list of ModelResult)

    The response always includes:
        request_id  -> traceability
        policy      -> gateway policy results
    """

    # Unique ID used for tracing the request across logs
    request_id: UUID

    # Gateway policy validation result
    policy: PolicyResult

    # Single-model response (kept for backward compatibility)
    answer: Optional[str] = None
    model_used: Optional[str] = None

    # Multi-model response results
    results: Optional[List[ModelResult]] = None