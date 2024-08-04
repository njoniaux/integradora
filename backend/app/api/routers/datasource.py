import os
import shutil
import asyncio
import aiofiles
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse  # Add this import
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
async def upload_files(files: List[UploadFile] = File(...), datasource_name: str = Form(...)):
    temp_dir = os.path.join(TEMP_UPLOAD_DIR, datasource_name)
    
    if os.path.exists(temp_dir):
        raise HTTPException(status_code=400, detail="Temporary datasource already exists")
    
    os.makedirs(temp_dir)
    
    file_paths = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        file_path = os.path.join(temp_dir, file.filename)
        # Handle duplicate filenames
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(file.filename)
            file_path = os.path.join(temp_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                content = await file.read()
                await buffer.write(content)
            file_paths.append(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    service_context = ServiceContext.from_defaults(
        chunk_size=DATASOURCES_CHUNK_SIZE,
        chunk_overlap=DATASOURCES_CHUNK_OVERLAP
    )
    
    try:
        await generateDatasource(service_context, datasource_name)
    except Exception as e:
        # If datasource generation fails, clean up the temporary directory
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Error generating datasource: {str(e)}")
    
    # Move files from temp directory to permanent datasource directory
    datasource_dir = os.path.join(DATASOURCES_DIR, datasource_name)
    shutil.move(temp_dir, datasource_dir)
    
    return JSONResponse(content={
        "message": f"Uploaded {len(files)} files and created datasource '{datasource_name}'",
        "datasource_name": datasource_name,
        "file_paths": file_paths
    })

async def generateDatasource(service_context: ServiceContext, datasource: str):
    ds_data_dir = os.path.join(TEMP_UPLOAD_DIR, datasource)
    ds_storage_dir = os.path.join(DATASOURCES_CACHE_DIR, datasource)
    print(f"Generating storage context for datasource '{datasource}'...")
    documents = SimpleDirectoryReader(ds_data_dir).load_data()
    index = await asyncio.to_thread(
        VectorStoreIndex.from_documents,
        documents,
        service_context=service_context,
        show_progress=True
    )
    await asyncio.to_thread(index.storage_context.persist, ds_storage_dir)
    print(f"Finished creating new index. Stored in {ds_storage_dir}")

@datasource_router.get("/list")
@role_required(["ADMIN", "TEACHER"])  # Adjust roles as needed
async def list_datasources():
    try:
        # Get all items in the DATASOURCES_DIR
        items = os.listdir(DATASOURCES_DIR)
        
        # Filter out non-directory items
        datasources = [item for item in items if os.path.isdir(os.path.join(DATASOURCES_DIR, item))]
        
        return JSONResponse(content={
            "datasources": datasources
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing datasources: {str(e)}")
