from langchain_anthropic import ChatAnthropic
from app.config import settings

llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    api_key=settings.ANTHROPIC_API_KEY,
    temperature=0.0
)