# nodes.py
"""
Agent workflow nodes - Currently minimal as flow is in main.py
Available for future AI-powered analysis nodes
"""

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.llms import Ollama
import os


def get_llm(llm_provider: str = "glm"):
    """Get LLM based on provider for AI feedback"""
    provider = llm_provider.lower()
    
    if provider == "openai":
        return ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
    
    elif provider == "azure":
        return AzureChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
    
    elif provider == "anthropic":
        return ChatAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), model="claude-3-opus-20240229")

    elif provider == "google":
        return ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), model="gemini-1.5-pro")

    elif provider in ["zhipu", "glm", "zai"]:
        return ChatZhipuAI(api_key=os.getenv("ZAI_API_KEY"), model="GLM-4.7-flash")

    elif provider == "ollama":
        return Ollama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3")
        )
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")