from codechat.interface.cli import CLI
from codechat.events.event_bus import bus
from codechat.events import types

def test_cli_user_input(monkeypatch):
    cli = CLI()
    called = {}
    def fake_print(msg):
        called['printed'] = msg
    monkeypatch.setattr("builtins.print", fake_print)
    bus.publish(types.USER_INPUT, "test input")
    assert "test input" in called['printed']
