from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAI

from app.config import settings


@lru_cache(maxsize=4)
def get_llm(temperature: float = 0.2) -> GoogleGenerativeAI:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env before making queries."
        )
    return GoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=temperature,
    )
