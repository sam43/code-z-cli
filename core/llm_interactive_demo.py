import os
from core.llm_interactive import LLMInteractiveSession

if __name__ == "__main__":
    model_name = os.environ.get("CODEZ_MODEL", "deepseek-r1:latest")
    db_path = os.path.join(os.path.dirname(__file__), '..', 'sessions', 'session_memory.db')
    llm = LLMInteractiveSession(model_name=model_name, db_path=db_path)
    print("Welcome to the interactive LLM session with fast SQLite memory. Type 'exit' to quit.")
    while True:
        user_input = input(">>> ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        response = llm.ask(user_input)
        print("Model:", response)
