from codechat.data.session_repository import SessionRepository
from codechat.domain.conversation import Message
import os
import tempfile

def test_session_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = SessionRepository(session_dir=tmpdir)
        messages = [Message(sender="user", content="Hi")] 
        repo.save("testsession", messages)
        loaded = repo.load("testsession")
        assert len(loaded) == 1
        assert loaded[0].content == "Hi"
