# app/schemas/ai_schema.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, List
from uuid import UUID

Decision = Literal["pass", "fail"]
DEFAULT_MODEL = "ollama:llama3"

class AIQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    model: Optional[str] = None
    models: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_model_choice(self):
        # cannot send both
        if self.model and self.models:
            raise ValueError("Provide either 'model' or 'models', not both.")

        # if models provided, it must not be empty
        if self.models is not None and len(self.models) == 0:
            raise ValueError("'models' must contain at least 1 model.")

        # if neither provided, default model
        if not self.model and not self.models:
            self.model = DEFAULT_MODEL

        return self

class PolicyResult(BaseModel):
    rbac: Decision
    size: Decision

class ModelResult(BaseModel):
    answer: str
    model_used: str

class AIQueryResponse(BaseModel):
    request_id: UUID
    policy: PolicyResult

    # single-mode response (backward compatible)
    answer: Optional[str] = None
    model_used: Optional[str] = None

    # multi-mode response
    results: Optional[List[ModelResult]] = None
