from typing import Annotated, Literal
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


class ProviderSettings(Input):
    enabled: bool = Field(strict=True)
    auth_mode: Literal['express_key', 'adc'] = 'express_key'
    api_key: str = Field(default='', max_length=512, repr=False)
    model: str = Field(default='', max_length=150, pattern=r'^[a-zA-Z0-9._-]*$')
    project: str = Field(default='', max_length=100, pattern=r'^[a-zA-Z0-9._:-]*$')
    location: str = Field(default='', max_length=60, pattern=r'^[a-zA-Z0-9-]*$')

    @field_validator('api_key')
    @classmethod
    def key_is_single_line(cls, value):
        if any(character.isspace() or not character.isascii() for character in value):
            raise ValueError('Paste one API key without spaces or line breaks.')
        return value


class ChatCreate(Input):
    mode: Literal['demo', 'google_cloud'] = 'demo'
    persona: Literal['guide', 'coach', 'concise'] = 'guide'


class ChatUpdate(Input):
    title: str = Field(min_length=1, max_length=80)
    persona: Literal['guide', 'coach', 'concise']


class ChatRetry(Input):
    request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{8,80}$")


class ChatSelection(Input):
    generation_id: str = Field(min_length=8, max_length=80)
    include_partial: bool = False


class EmptyInput(Input):
    pass


class ChatContext(Input):
    message: str = Field(default='', max_length=4000)


Feature = Annotated[float, Field(ge=0, le=10, allow_inf_nan=False, strict=True)]
ManualScore = Annotated[float, Field(ge=-3, le=3, allow_inf_nan=False, strict=True)]


class SimilarityToy(Input):
    vector: list[Feature] = Field(min_length=3,max_length=3)


class AttentionToy(Input):
    scores: list[ManualScore] = Field(min_length=7,max_length=7)
    query_index: int = Field(ge=0,le=6,strict=True)
    causal: bool = Field(default=True,strict=True)
    temperature: float = Field(default=1, ge=.25, le=2, allow_inf_nan=False, strict=True)


class TrainingToy(Input):
    weight: float = Field(default=1, ge=0, le=6, allow_inf_nan=False, strict=True)
    learning_rate: float = Field(default=.25, ge=.05, le=1, allow_inf_nan=False, strict=True)
    steps: int = Field(default=1,ge=1,le=10,strict=True)
    operation: Literal['predict','train'] = 'predict'
