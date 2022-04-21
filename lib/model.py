from typing import TypedDict, Any


class SlowmodeType(TypedDict):
    user_id: int
    duration: int
    duration_unit: str
    interval: int
    interval_unit: str
    reason: Any
    channel_id: Any
    issued_by: str
    issued_at: float


class Event(TypedDict):
    name: str
    author_id: int
    description: str
    time: int
    role: Any
    utc_time: float
