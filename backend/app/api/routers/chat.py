from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.api.routers.auth import get_current_user, User
from openai import OpenAI
from app.utils.index import get_index
from llama_index import ServiceContext
from llama_index.llms.openai import OpenAI as LlamaOpenAI

chat_router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatData(BaseModel):
    message: str
    messages: Optional[List[Message]] = None
    datasource: Optional[str] = None

client = OpenAI()

@chat_router.post("")
async def chat(
    data: ChatData,
    current_user: User = Depends(get_current_user)
):
    if not data.datasource:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No datasource provided",
        )

    messages = [{"role": m.role, "content": m.content} for m in (data.messages or [])]

    service_context = ServiceContext.from_defaults(llm=LlamaOpenAI(model="gpt-3.5-turbo-16k"))
    index = get_index(service_context, data.datasource)
    query_engine = index.as_query_engine()
    context_response = query_engine.query(data.message)

    context_message = f"CONTEXT: {context_response}\n\nUSER QUERY: {data.message}"
    messages.append({"role": "user", "content": context_message})

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        assistant_message = completion.choices[0].message.content

        messages.append({"role": "assistant", "content": assistant_message})

        return {
            "response": assistant_message,
            "messages": messages
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in OpenAI API call: {str(e)}"
        )
