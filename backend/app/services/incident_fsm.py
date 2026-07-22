STATES = ["pending_review", "confirmed", "in_progress", "closed"]

TRANSITIONS = {
    "pending_review": ["confirmed"],
    "confirmed": ["in_progress", "closed"],
    "in_progress": ["closed"],
    "closed": [],
}


def validate_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, [])
