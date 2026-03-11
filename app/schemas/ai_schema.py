# app/schemas/ai_schema.py

from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

Decision = Literal["pass", "fail"]
DEFAULT_MODEL = "ollama:llama3"


class AIQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    model: Optional[str] = None
    models: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_model_choice(self):
        if self.model and self.models:
            raise ValueError("Provide either 'model' or 'models', not both.")
        if self.models is not None and len(self.models) == 0:
            raise ValueError("'models' must contain at least 1 model.")
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

    # Single-model response (backward compatible with /ai/query)
    answer: Optional[str] = None
    model_used: Optional[str] = None

    # Multi-model response
    results: Optional[List[ModelResult]] = None
