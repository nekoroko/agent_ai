# config.py — LM Studio接続設定
from langchain_openai import ChatOpenAI

LM_STUDIO_BASE_URL = "http://10.0.2.2:1234/v1"
LM_STUDIO_MODEL = "gemma-4-26b-a4b-it"

def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    """LM Studioに接続するLLMインスタンスを返す"""
    return ChatOpenAI(
        model=LM_STUDIO_MODEL,
        base_url=LM_STUDIO_BASE_URL,
        api_key="lm-studio",
        temperature=temperature,
    )