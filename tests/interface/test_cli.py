from cli import CLI
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


# def run(self):
#         while True:
#             choice = input("Choose mode: [A]Ask or [B]Assist >> ").strip().lower()
#             if choice in ['a', 'b']:
#                 break
#             else:
#                 print("Invalid choice. Please enter 'A' or 'B'.")

#         if choice == 'a':
#             prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts', 'ask_system_prompt.txt')
#             with open(prompt_file_path, 'r', encoding='utf-8') as f:
#                 prompt = f.read()
#             save_system_prompt(prompt)
#             prompt_indicator = "Ask >>"

#         elif choice == 'b':
#             prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts', 'assist_system_prompt.txt')
#             with open(prompt_file_path, 'r', encoding='utf-8') as f:
#                 prompt = f.read()
#             save_system_prompt(prompt)
#             prompt_indicator = "Assist >>"

#         while True:
#             user_input = input(prompt_indicator)
#             if user_input.strip() == "/endit":
#                 bus.publish(types.SESSION_SAVE, "session_001")
#                 break
#             bus.publish(types.USER_INPUT, user_input)