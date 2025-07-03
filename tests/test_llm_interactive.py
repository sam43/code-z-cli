# Example test for LLMInteractiveSession
from core.llm_interactive import LLMInteractiveSession

def test_llm_interactive():
    llm = LLMInteractiveSession(model_name="deepseek-r1:latest")
    response = llm.ask("Say hello!")
    assert isinstance(response, str)
    print("Test passed. Model response:", response)

if __name__ == "__main__":
    test_llm_interactive()
