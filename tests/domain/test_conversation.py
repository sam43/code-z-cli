import pytest
from codechat.domain.conversation import Message, Conversation

def test_conversation_add_and_history():
    conv = Conversation()
    msg = Message(sender="user", content="Hello")
    conv.add_message(msg)
    history = conv.get_history()
    assert len(history) == 1
    assert history[0].sender == "user"
    assert history[0].content == "Hello"
