import pytest
from core.llm_interactive import LLMInteractiveSession
import tempfile
import os

def test_context_persistence_between_turns():
    session = LLMInteractiveSession(model_name="test-model", persist=False)
    session.memory.add_turn("hello", "hi")
    session.memory.add_turn("what's up?", "not much")
    context = session.memory.get_context()
    assert context[-1]["user"] == "what's up?"
    assert context[-1]["response"] == "not much"
    prompt = session.memory.get_context_prompt()
    assert "hello" in prompt and "what's up?" in prompt

def test_sqlite_context_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        session = LLMInteractiveSession(model_name="test-model", db_path=db_path, persist=True)
        session.memory.add_turn("foo", "bar")
        session.memory.add_turn("baz", "qux")
        prompt = session.memory.get_context_prompt()
        assert "foo" in prompt and "baz" in prompt
        session.memory.clear()
        assert session.memory.get_context() == []

def test_context_clear():
    session = LLMInteractiveSession(model_name="test-model", persist=False)
    session.memory.add_turn("a", "b")
    session.memory.clear()
    assert session.memory.get_context() == []
