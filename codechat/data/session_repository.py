"""
Data layer: session and file IO, repositories.
"""
import os
import json
from typing import List
from codechat.domain.conversation import Message

SESSION_DIR = os.path.join(os.path.dirname(__file__), '../../sessions')

class SessionRepository:
    def __init__(self, session_dir=SESSION_DIR):
        self.session_dir = os.path.abspath(session_dir)
        os.makedirs(self.session_dir, exist_ok=True)
    def save(self, session_id: str, messages: List[Message]):
        with open(os.path.join(self.session_dir, f"{session_id}.json"), 'w') as f:
            json.dump([m.__dict__ for m in messages], f)
    def load(self, session_id: str) -> List[Message]:
        with open(os.path.join(self.session_dir, f"{session_id}.json"), 'r') as f:
            data = json.load(f)
            return [Message(**m) for m in data]
