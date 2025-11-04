from langchain_google_genai import ChatGoogleGenerativeAI


def load_google_generative_ai_model(
    model_name: str = "gemini-2.5-flash", temperature: float = 0
) -> ChatGoogleGenerativeAI:
    """Inicializa e retorna um modelo de linguagem ChatGoogleGenerativeAI.

    Args:
        model_name (str): Nome do modelo a ser utilizado.
        temperature (float): Temperatura para controle de aleatoriedade.

    Returns:
        ChatGoogleGenerativeAI: Instância do modelo de linguagem inicializado.
    """
    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
