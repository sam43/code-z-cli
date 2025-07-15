"""
Interface layer: CLI, REPL, and event adapters.
"""
from codechat.events.event_bus import bus
from codechat.events import types
from codechat.domain.conversation import Message, Conversation
from codechat.data.session_repository import SessionRepository
from core.user_config import save_system_prompt, clear_model_choice
from rich.console import Console
from rich.text import Text
import toml
import os
import argparse

def get_version():
    pyproject_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'pyproject.toml')
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        data = toml.load(f)
    return data['project']['version']

class CLI:
    VERSION = get_version()
    def __init__(self):
        self.conversation = Conversation()
        self.session_repo = SessionRepository()
        bus.subscribe(types.USER_INPUT, self.handle_user_input)
        bus.subscribe(types.SESSION_SAVE, self.handle_session_save)
        self.console = Console()

    def print_banner(self):
        banner = '''\n  ______          __  _____      ________    ____  \n / ____/___  ____/ /_/__  /     / ____/ /   /  _/  \n/ /   / __ \/ __  / _ \/ /     / /   / /    / /    \n/ /___/ /_/ / /_/ /  __/ /__  / /___/ /____/ /     \n\____/\____/\__,_/\___/____/  \____/_____/___/      \n'''
        tagline = "When AI Takes a Break, We Don’t!  █████████████████████████████████████████████████████████████"
        version = Text(f"v{self.VERSION}", style="bold cyan")
        self.console.print(banner, style="bold cyan")
        self.console.print("[bold magenta]         CodeZ CLI – When AI Takes a Break, We Don’t![/bold magenta]", justify="center")
        self.console.print(f"[yellow]{tagline}[/yellow]", justify="center")
        self.console.print(version, justify="center")
        self.console.print()

    def handle_user_input(self, content):
        msg = Message(sender="user", content=content)
        self.conversation.add_message(msg)
        print(f"[user]: {content}")
        # Here you would trigger LLM/model, then publish SYSTEM_OUTPUT
    def handle_session_save(self, session_id):
        self.session_repo.save(session_id, self.conversation.get_history())
        print(f"Session {session_id} saved.")
    def run(self):
        self.print_banner()

        while True:
            choice = input("Choose mode: [A]sk or [B]ssist >> ").strip().lower()
            if choice in ['a', 'b']:
                break
            else:
                print("Invalid choice. Please enter 'A' or 'B'.")

        if choice == 'a':
            prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts', 'ask_system_prompt.txt')
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            save_system_prompt(prompt)
            prompt_indicator = "Ask >>"

        elif choice == 'b':
            prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts', 'assist_system_prompt.txt')
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            save_system_prompt(prompt)
            prompt_indicator = "Assist >>"

        while True:
            user_input = input(prompt_indicator)
            if user_input.strip() == "/endit":
                bus.publish(types.SESSION_SAVE, "session_001")
                break
            bus.publish(types.USER_INPUT, user_input)
