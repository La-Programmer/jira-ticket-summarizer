from enum import Enum

class LlmProviderEnum(str, Enum):
    """Supported LLM providers for the summarization service."""
    OPENAI = "openai"
    GROQ = "groq"
