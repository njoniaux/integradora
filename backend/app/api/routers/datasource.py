import os
import shutil
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from llama_index import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from app.constants import (
    DATASOURCES_CACHE_DIR,
    DATASOURCES_DIR,
    DATASOURCES_CHUNK_SIZE,
    DATASOURCES_CHUNK_OVERLAP,
)
from app.api.routers.auth import role_required

datasource_router = APIRouter()

TEMP_UPLOAD_DIR = "temp_uploads"

@datasource_router.post("/upload")
@role_required(["ADMIN", "TEACHER"])
async def upload_files(files: List[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())
    session_upload_dir = os.path.join(TEMP_UPLOAD_DIR, session_id)
    
    if not os.path.exists(session_upload_dir):
        os.makedirs(session_upload_dir)
    
    file_paths = []
    for file in files:
        file_path = os.path.join(session_upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_path)
    
    return JSONResponse(content={
        "message": f"Uploaded {len(files)} files",
        "session_id": session_id,
        "file_paths": file_paths
    })

@datasource_router.post("/create")
@role_required(["ADMIN", "TEACHER"])
async def create_datasource(name: str, session_id: str):
    session_upload_dir = os.path.join(TEMP_UPLOAD_DIR, session_id)
    
    if not os.path.exists(session_upload_dir):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    datasource_dir = os.path.join(DATASOURCES_DIR, name)
    if os.path.exists(datasource_dir):
        raise HTTPException(status_code=400, detail="Datasource already exists")
    
    # Move files from temp session directory to datasource directory
    shutil.move(session_upload_dir, datasource_dir)
    
    service_context = ServiceContext.from_defaults(
        chunk_size=DATASOURCES_CHUNK_SIZE,
        chunk_overlap=DATASOURCES_CHUNK_OVERLAP
    )
    
    generateDatasource(service_context, name)
    
    return JSONResponse(content={"message": f"Created datasource '{name}'"})

@datasource_router.get("/list")
@role_required(["ADMIN", "TEACHER"])
async def list_datasources():
    datasources = [d for d in os.listdir(DATASOURCES_DIR) if os.path.isdir(os.path.join(DATASOURCES_DIR, d))]
    return JSONResponse(content={"datasources": datasources})

def generateDatasource(service_context: ServiceContext, datasource: str):
    ds_data_dir = os.path.join(DATASOURCES_DIR, datasource)
    ds_storage_dir = os.path.join(DATASOURCES_CACHE_DIR, datasource)
    print(f"Generating storage context for datasource '{datasource}'...")
    documents = SimpleDirectoryReader(ds_data_dir).load_data()
    index = VectorStoreIndex.from_documents(
        documents, service_context=service_context, show_progress=True
    )
    index.storage_context.persist(ds_storage_dir)
    print(f"Finished creating new index. Stored in {ds_storage_dir}")

@datasource_router.get("/{datasource_name}")
@role_required(["ADMIN", "TEACHER"])
async def get_datasource_details(datasource_name: str):
    datasource_dir = os.path.join(DATASOURCES_DIR, datasource_name)
    cache_dir = os.path.join(DATASOURCES_CACHE_DIR, datasource_name)
    
    if not os.path.exists(datasource_dir) or not os.path.exists(cache_dir):
        raise HTTPException(status_code=404, detail=f"Datasource '{datasource_name}' not found")
    
    # You can add more details here if needed, such as number of documents, creation date, etc.
    return JSONResponse(content={
        "name": datasource_name,
        "status": "ready"
    })