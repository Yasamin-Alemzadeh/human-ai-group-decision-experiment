import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, field_validator


class ExperimentConfig(BaseModel):
    condition: str
    participants: list[Literal["human", "ai"]]
    rounds: int = 2
    discussion_seconds: int = 60
    voting_seconds: int = 15
    allow_self_vote: bool = True
    show_round_feedback: bool = True

    @field_validator("participants")
    @classmethod
    def exactly_three(cls, v):
        if len(v) != 3:
            raise ValueError("participants must contain exactly 3 entries")
        return v


class AIConfig(BaseModel):
    provider: Literal["anthropic", "mock"] = "mock"
    model: str = "claude-haiku-5-5"
    reply_delay_seconds: tuple[float, float] = (2.0, 6.0)
    max_messages_per_round: int = 3
    llm_timeout_seconds: float = 5.0


class Config(BaseModel):
    experiment: ExperimentConfig
    ai: AIConfig = AIConfig()


def load_config(path: str | None = None) -> Config:
    p = Path(path or os.getenv("CONFIG_PATH", "config.yml"))
    return Config(**yaml.safe_load(p.read_text()))