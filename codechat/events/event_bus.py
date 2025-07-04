"""
In-memory event bus for pub-sub event-driven architecture.
"""
from collections import defaultdict
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, data: Any = None):
        for handler in self._subscribers[event_type]:
            handler(data)

# Singleton event bus instance
bus = EventBus()
