"""LLM utilities module.

This module provides utilities for loading and configuring
Large Language Models.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama


def load_google_generative_ai_model(
    model_name: str = "gemini-2.5-pro", temperature: float = 0
) -> ChatGoogleGenerativeAI:
    """Initialize and return a ChatGoogleGenerativeAI language model.

    Args:
        model_name: Name of the model to be used
        temperature: Temperature setting for the model

    Returns:
        Instance of the configured language model
    """
    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)


def load_ollama_model(
    models_name: str,
    temperature: float = 0,
) -> ChatOllama:
    """Initialize and return a ChatOllama language model.

    Args:
        models_name: Name of the model to be used
        temperature: Temperature setting for the model

    Returns:
        Instance of the configured language model
    """
    return ChatOllama(model=models_name, temperature=temperature)
