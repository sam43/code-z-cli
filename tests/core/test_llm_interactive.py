import pytest
from core.llm_interactive import LLMInteractiveSession
import os
import tempfile

def test_inmemory_session_add_and_context():
    session = LLMInteractiveSession(model_name="test-model", persist=False, max_token_budget=1000)
    session.ask = lambda x: f"Echo: {x}"  # Mock model
    session.memory.add_turn("hi", "Echo: hi")
    session.memory.add_turn("how are you?", "Echo: how are you?")
    prompt = session.memory.get_context_prompt()
    assert "hi" in prompt and "how are you?" in prompt

def test_sqlite_session_add_and_context():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        session = LLMInteractiveSession(model_name="test-model", db_path=db_path, persist=True, max_token_budget=1000)
        session.ask = lambda x: f"Echo: {x}"  # Mock model
        session.memory.add_turn("hi", "Echo: hi")
        session.memory.add_turn("how are you?", "Echo: how are you?")
        prompt = session.memory.get_context_prompt()
        assert "hi" in prompt and "how are you?" in prompt
        session.memory.clear()
        assert session.memory.get_context() == []

def test_token_budget_truncation():
    session = LLMInteractiveSession(model_name="test-model", persist=False, max_token_budget=5, token_estimator=lambda s: len(s.split()))
    for i in range(10):
        session.memory.add_turn(f"q{i}", f"a{i}")
    prompt = session.memory.get_context_prompt()
    # Only the most recent turns should fit
    assert "q9" in prompt and "a9" in prompt
    assert "q0" not in prompt
