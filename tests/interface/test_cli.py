from cli import CLI
from codechat.events.event_bus import bus
from codechat.events import types

def test_cli_user_input(monkeypatch):
    cli = CLI()
    called = {}
    def fake_print(msg):
        """
        Capture the printed message by storing it in the 'called' dictionary under the 'printed' key.
        
        Parameters:
            msg (str): The message to capture.
        """
        called['printed'] = msg
    monkeypatch.setattr("builtins.print", fake_print)
    bus.publish(types.USER_INPUT, "test input")
    assert "test input" in called['printed']