from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Sequence
from app.api.routers.auth import get_current_user, User
from app.utils.index import get_index
from llama_index import ServiceContext
from llama_index.llms.openai import OpenAI
from llama_index.llms.base import ChatMessage, MessageRole

chat_router = APIRouter()

class LLMConfig(BaseModel):
    model: str
    temperature: Optional[float] = None
    topP: Optional[float] = None
    maxTokens: int = 2000

class Embedding(BaseModel):
    text: str
    embedding: Sequence[float]

class ChatData(BaseModel):
    message: str
    messages: Optional[Sequence[ChatMessage]] = None
    datasource: Optional[str] = None
    config: Optional[LLMConfig] = None
    embeddings: Optional[Sequence[Embedding]] = None

def llm_from_config(config: Optional[LLMConfig]):
    if config:
        return OpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.maxTokens,
        )
    else:
        return OpenAI(model="gpt-4")

@chat_router.post("")
async def chat(
    data: ChatData,
    current_user: User = Depends(get_current_user)
):
    service_context = ServiceContext.from_defaults(llm=llm_from_config(data.config))
    
    if not data.datasource:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No datasource provided",
        )

    index = get_index(service_context, data.datasource)
    
    messages = data.messages or []

    chat_engine = index.as_chat_engine()
    response = chat_engine.stream_chat(data.message, messages)

    async def event_generator():
        for token in response.response_gen:
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")