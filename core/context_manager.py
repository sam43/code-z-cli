import os
import json

class ContextManager:
    def __init__(self, session_file=None, max_turns=20):
        self.max_turns = max_turns
        self.session = []
        self.session_file = session_file
        if session_file and os.path.exists(session_file):
            with open(session_file, "r") as f:
                try:
                    self.session = json.load(f)
                except Exception:
                    self.session = []

    def add_turn(self, user, response):
        self.session.append({"user": user, "response": response})
        if len(self.session) > self.max_turns:
            self.session = self.session[-self.max_turns:]
        if self.session_file:
            with open(self.session_file, "w") as f:
                json.dump(self.session, f, indent=2)

    def get_context(self):
        return self.session

    def get_context_prompt(self):
        """Return a prompt string representing the current session context for the LLM."""
        context = self.get_context()
        if not context:
            return ""
        prompt = ""
        for turn in context:
            prompt += f"User: {turn['user']}\nModel: {turn['response']}\n"
        return prompt.strip()

    def clear(self):
        self.session = []
        if self.session_file and os.path.exists(self.session_file):
            os.remove(self.session_file)
