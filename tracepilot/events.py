import datetime
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class TimelineEvent:
    id: int
    timestamp: str
    type: str         # 'routing', 'failure', 'learning', 'system'
    title: str
    description: str
    metrics: Optional[Dict[str, Any]] = None

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_TIMELINE_FILE = os.path.join(_DATA_DIR, "timeline.json")

def _load_events() -> List[Dict[str, Any]]:
    if not os.path.exists(_TIMELINE_FILE):
        return []
    try:
        with open(_TIMELINE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_events(events: List[Dict[str, Any]]) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_TIMELINE_FILE, "w") as f:
        json.dump(events, f, indent=2)

def emit_event(type: str, title: str, description: str, metrics: Optional[Dict[str, Any]] = None) -> None:
    events = _load_events()
    
    event = TimelineEvent(
        id=len(events) + 1,
        timestamp=datetime.datetime.now().isoformat(),
        type=type,
        title=title,
        description=description,
        metrics=metrics
    )
    events.append(asdict(event))
    _save_events(events)
    
def get_events() -> List[Dict[str, Any]]:
    return _load_events()

def clear_events() -> None:
    _save_events([])
