import sqlite3
import os
from typing import List, Dict, Optional, Callable

class SQLiteSessionMemory:
    """
    SQLite-backed session memory for chat history, supporting token-aware context window.
    Stores (user, response) turns and can return a prompt containing as much history as fits within a token budget.
    """
    def __init__(self, db_path: str, max_token_budget: int = 3000, token_estimator: Optional[Callable[[str], int]] = None):
        self.db_path = db_path
        self.max_token_budget = max_token_budget
        # Token estimator: function that takes a string and returns estimated token count
        # Default: word count * 1.3
        self.token_estimator = token_estimator or (lambda s: int(len(s.split()) * 1.3))
        self._ensure_db()

    def _ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS session (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    response TEXT NOT NULL
                )
            ''')

    def add_turn(self, user: str, response: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO session (user, response) VALUES (?, ?)',
                (user, response)
            )
            # No hard limit on turns; context window is managed by token budget

    def get_context(self) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                'SELECT user, response FROM session ORDER BY id ASC'
            ).fetchall()
        return [{"user": user, "response": response} for user, response in rows]

    def get_context_prompt(self) -> str:
        """
        Returns a chat-formatted prompt containing as much history as fits within the token budget.
        Oldest turns are truncated if needed to fit the budget.
        """
        context = self.get_context()
        prompt_turns = []
        total_tokens = 0
        # Build up prompt from most recent to oldest, then reverse at the end
        for turn in reversed(context):
            turn_str = f"User: {turn['user']}\nModel: {turn['response']}\n"
            turn_tokens = self.token_estimator(turn_str)
            if total_tokens + turn_tokens > self.max_token_budget:
                break
            prompt_turns.append(turn_str)
            total_tokens += turn_tokens
        # Reverse to get oldest-to-newest order
        prompt = ''.join(reversed(prompt_turns)).strip()
        return prompt

    def clear(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM session')
