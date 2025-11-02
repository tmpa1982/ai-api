from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from storage_account import AzureStorageAccount
from auth_utils import check_role
from vector_store import upload_files

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
