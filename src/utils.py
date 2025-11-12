from langchain_google_genai import ChatGoogleGenerativeAI


def load_google_generative_ai_model(
    model_name: str = "gemini-2.5-pro", temperature: float = 0
) -> ChatGoogleGenerativeAI:
    """
    Initializes and returns a ChatGoogleGenerativeAI language model.

    Args:
        model_name (str): Name of the model to be used.
        temperature (float): Temperature setting for the model.

    Returns:
        ChatGoogleGenerativeAI: Instance of the configured language model.
    """
    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
