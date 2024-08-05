import logging
import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from app.api.routers.chat import chat_router
from app.api.routers.datasource import datasource_router
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from app.api.routers.auth import auth_router

load_dotenv()

app = FastAPI()

environment = os.getenv("ENVIRONMENT", "dev")

if environment == "dev":
    logger = logging.getLogger("uvicorn")
    logger.warning("Running in development mode - allowing CORS for all origins")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(chat_router, prefix="/api/chat")
app.include_router(datasource_router, prefix="/datasource", tags=["datasource"])
app.include_router(auth_router, prefix='/auth')

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", reload=True)
