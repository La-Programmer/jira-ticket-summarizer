# services/llm_factory.py
import os
from typing import Optional
from langchain_openai import ChatOpenAI 
from langchain_groq import ChatGroq

from enums.llm_provider_enums import LlmProviderEnum

def get_llm(
    provider: Optional[LlmProviderEnum] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
):
    """
    Factory function to return a LangChain-compatible LLM client.
    Supports OpenAI and Groq providers.

    Args:
        provider: "openai" or "groq" (default: "openai")
        model: model name (optional)
        temperature: sampling temperature (default 0.2)
    """
    provider = (provider or os.getenv("LLM_PROVIDER") or LlmProviderEnum.OPENAI).lower()
    temperature = temperature if temperature is not None else 0.2

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment.")
        model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            openai_api_key=api_key,
            model=model_name,
            temperature=temperature,
            streaming=False,
        )

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in environment.")
        model_name = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(
            groq_api_key=api_key,
            model=model_name,
            temperature=temperature,
            streaming=False,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
