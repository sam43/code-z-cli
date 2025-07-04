"""
Domain layer: business logic, entities, and use cases.
"""
# Example entity and use case
class Message:
    def __init__(self, sender: str, content: str):
        self.sender = sender
        self.content = content

class Conversation:
    def __init__(self):
        self.messages = []
    def add_message(self, message: Message):
        self.messages.append(message)
    def get_history(self):
        return self.messages
