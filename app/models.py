from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Attempt(Input):
    lesson_id: str = Field(pattern=r"^L\d{2}$")
    version: int = Field(ge=1, strict=True)
    activity_id: str = Field(min_length=1, max_length=100)
    answers: dict[str, str] = Field(default_factory=dict, max_length=3)
    study: bool = False
    idempotency_key: str = Field(min_length=8, max_length=100)


class Acknowledgment(Input):
    kind: Literal["reading", "build"]
    version: int = Field(ge=1, strict=True)


class Journal(Input):
    lesson_id: str = Field(pattern=r"^L\d{2}$")
    changed: str = Field(min_length=1, max_length=2000)
    learned: str = Field(min_length=1, max_length=2000)
    confusing: str = Field(default="", max_length=2000)


class DemoMessage(Input):
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Write a message first.")
        return value


class AIMessage(Input):
    message: str = Field(min_length=1, max_length=4000)
    request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{8,80}$")


class TutorMessage(AIMessage):
    lesson_id: str = Field(pattern=r"^L\d{2}$")
    version: int = Field(ge=1, strict=True)
    mode: Literal["hint", "explain", "solution"] = "hint"


class ConnectionTest(Input):
    request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{8,80}$")
