from dataclasses import dataclass, field
from enum import Enum
import time


class Phase(str, Enum):
    WAITING = "waiting"
    DISCUSSION = "discussion"
    VOTING = "voting"
    RESULTS = "results"


@dataclass
class Slot:
    player_id: str           # "A" | "B" | "C"
    kind: str                # "human" | "ai"  (server-side only, never sent to clients)
    joined: bool = False


@dataclass
class Message:
    player: str
    text: str
    round: int
    ts: float = field(default_factory=time.time)


@dataclass
class Result:
    winner: str
    counts: dict[str, int]       #  final-round vote counts
    tie_break: str               # "none" | "cumulative" | "random"