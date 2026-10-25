import os


from langchain_ollama import ChatOllama


def get_llm():
    """
    Get the LLM instance based on the environment variable.
    """

    # Get the model name from the environment variable
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    # Create and return the ChatOllama instance
    return ChatOllama(model=model_name)