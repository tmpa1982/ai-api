from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from storage_account import AzureStorageAccount
from auth_utils import check_role
from vector_store import upload_files
import os
from logging_config import logging

router = APIRouter()

@router.post("/upload/vector_store")
async def upload_vector_store(user = Depends(check_role("APIUser"))):
    result = upload_files()
    return result

@router.post("/upload/storage_account")
async def upload_storage_account(
    file: UploadFile = File(...),
    user = Depends(check_role("APIUser"))
):
    container_name = "knowledgestore"
    try:
        data = await file.read()
        blob_prefix = "cv"
        blob_name = f"{blob_prefix}/{file.filename}"
        storage = AzureStorageAccount()
        storage.upload_file(container_name, blob_name, data)
        return {
            "status": "success",
            "container": container_name,
            "blob": blob_name,
            "size_bytes": len(data),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    logging.info(f"Received: {file.filename}, {file.content_type}")
    upload_dir = ".upload"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(".upload", "received_chunk.webm")
    contents = await file.read()
    with open(file_path, "ab") as f:
        f.write(contents)
    return {"status": "ok", "filename": file.filename, "size": len(contents)}
