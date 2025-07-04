"""
Interface layer: CLI, REPL, and event adapters.
"""
from codechat.events.event_bus import bus
from codechat.events import types
from codechat.domain.conversation import Message, Conversation
from codechat.data.session_repository import SessionRepository

class CLI:
    def __init__(self):
        self.conversation = Conversation()
        self.session_repo = SessionRepository()
        bus.subscribe(types.USER_INPUT, self.handle_user_input)
        bus.subscribe(types.SESSION_SAVE, self.handle_session_save)
    def handle_user_input(self, content):
        msg = Message(sender="user", content=content)
        self.conversation.add_message(msg)
        print(f"[user]: {content}")
        # Here you would trigger LLM/model, then publish SYSTEM_OUTPUT
    def handle_session_save(self, session_id):
        self.session_repo.save(session_id, self.conversation.get_history())
        print(f"Session {session_id} saved.")
    def run(self):
        while True:
            user_input = input("You: ")
            if user_input.strip() == "/endit":
                bus.publish(types.SESSION_SAVE, "session_001")
                break
            bus.publish(types.USER_INPUT, user_input)
