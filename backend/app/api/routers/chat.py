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

# Define the service context and default index outside the route
service_context = ServiceContext.from_defaults(llm=LlamaOpenAI(model="gpt-3.5-turbo-16k"))
default_datasource = "fundamentos_programacion"
default_index = get_index(service_context, default_datasource)

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

    # Prepare the messages for the API call
    messages = [{"role": m.role, "content": m.content} for m in (data.messages or [])]

    # Use the default index or get a new one if the datasource is different
    if data.datasource != default_datasource:
        index = get_index(service_context, data.datasource)
    else:
        index = default_index

    query_engine = index.as_query_engine()
    context_response = query_engine.query(data.message)

    # Add the context and user message to the messages list
    context_message = f"CONTEXT: {context_response}\n\nUSER QUERY: {data.message}"
    messages.append({"role": "user", "content": context_message})

    try:
        # Make the API call to OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # or your preferred model
            messages=messages
        )

        # Extract the assistant's response
        assistant_message = completion.choices[0].message.content

        # Add the assistant's response to the message history
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