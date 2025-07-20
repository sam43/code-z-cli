from core.sqlite_memory import SQLiteSessionMemory
from core import model
from core.user_config import load_system_prompt
import os
import math

class LLMInteractiveSession:
    """
    LLM session with robust, token-aware context memory.
    Supports SQLite or in-memory, and configurable token budget.
    """
    def __init__(self, model_name, db_path=None, max_token_budget=None, persist=True, token_estimator=None):
        """
        Initialize an interactive LLM session with configurable context memory and token budget.
        
        Parameters:
            model_name (str): Name of the LLM model to use.
            db_path (str, optional): Path to the SQLite database for persistent session storage. Used only if persistence is enabled.
            max_token_budget (int, optional): Maximum number of tokens to retain in session context. Defaults to 3000 or the value of the CODEZ_MAX_TOKEN_BUDGET environment variable.
            persist (bool, optional): Whether to use persistent (SQLite) or in-memory session memory. Defaults to True.
            token_estimator (callable, optional): Function to estimate token count for a given text. If not provided, a default estimator is used.
        
        The system prompt is loaded from external configuration and prepended to each prompt sent to the model. Session memory is managed according to the specified persistence and token budget settings.
        """
        self.model_name = model_name
        self.persist = persist
        self.max_token_budget = max_token_budget or int(os.environ.get("CODEZ_MAX_TOKEN_BUDGET", 3000))
        self.token_estimator = token_estimator
        self.system_prompt = load_system_prompt()
        if persist:
            if db_path is None:
                db_path = os.path.join(os.path.dirname(__file__), '..', 'sessions', 'session_memory.db')
            self.memory = SQLiteSessionMemory(db_path, max_token_budget=self.max_token_budget, token_estimator=token_estimator)
        else:
            self.memory = InMemorySessionMemory(max_token_budget=self.max_token_budget, token_estimator=token_estimator)

    def ask(self, user_input):
        """
        Send a user input to the language model, incorporating the system prompt and recent conversation context, and return the model's response.
        
        The method constructs a prompt by combining the system prompt, the current session context within the token budget, and the new user input. It then queries the language model and records the exchange in session memory.
        
        Parameters:
            user_input (str): The user's message to send to the language model.
        
        Returns:
            str: The language model's response to the user input.
        """
        context_prompt = self.memory.get_context_prompt()
        prompt = f"{self.system_prompt or ''}\n{context_prompt}\nUser: {user_input}\nModel:"
        response = model.query_ollama(prompt, self.model_name)
        self.memory.add_turn(user_input, response)
        return response

    def clear(self):
        self.memory.clear()

class InMemorySessionMemory:
    """
    In-memory session memory for LLM chat, with token-aware context window.
    """
    def __init__(self, max_token_budget=3000, token_estimator=None):
        self.max_token_budget = max_token_budget
        self.token_estimator = token_estimator or self._default_token_estimator
        self.session = []

    def add_turn(self, user, response):
        self.session.append({"user": user, "response": response})

    def get_context(self):
        return self.session

    def get_context_prompt(self):
        prompt_turns = []
        total_tokens = 0
        for turn in reversed(self.session):
            turn_str = f"User: {turn['user']}\nModel: {turn['response']}\n"
            turn_tokens = self.token_estimator(turn_str)
            if total_tokens + turn_tokens > self.max_token_budget:
                break
            prompt_turns.append(turn_str)
            total_tokens += turn_tokens
        prompt_turns = list(reversed(prompt_turns))
        return ''.join(prompt_turns).strip()

    def clear(self):
        self.session = []

    @staticmethod
    def _default_token_estimator(text: str) -> int:
        return math.ceil(len(text.split()) * 1.3)
