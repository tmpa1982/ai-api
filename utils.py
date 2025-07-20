from openai import OpenAI
import os

from akv import AzureKeyVault
from storage_account import AzureStorageAccount

akv = AzureKeyVault()
openai_key = akv.get_secret("openai-apikey")
client = OpenAI(api_key=openai_key)

storage = AzureStorageAccount()

def upload_files():
    try:
        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".download")
        os.makedirs(download_dir, exist_ok=True)

        blobs = storage.list_blobs(container_name="knowledgestore", prefix="cv")

        results = []
        for blob_name in blobs:
            file_name = os.path.basename(blob_name)
            download_path = os.path.join(download_dir, file_name)

            storage.get_file(
                container_name="knowledgestore",
                blob_name=blob_name,
                download_path=download_path
            )

            try:
                file_response = client.files.create(file=open(download_path, 'rb'), purpose="assistants")
                attach_response = client.vector_stores.files.create(
                    vector_store_id=vector_store["id"],
                    file_id=file_response.id
                )
                results.append({"file": file_name, "status": "success"})
            except Exception as e:
                print(f"Error with {file_name}: {str(e)}")
                results.append({"file": file_name, "status": "failed", "error": str(e)})

        return results
    except Exception as e:
        print(f"Error during file upload: {str(e)}")
        return {"status": "failed", "error": str(e)}

def create_vector_store(store_name: str) -> dict:
    try:
        vector_store = client.vector_stores.create(name=store_name)
        details = {
            "id": vector_store.id,
            "name": vector_store.name,
            "created_at": vector_store.created_at,
            "file_count": vector_store.file_counts.completed
        }
        print("Vector store created:", details)
        return details
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return {}

vector_store = create_vector_store("Knowledge Base")

def upload_files():
    try:
        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".download")
        os.makedirs(download_dir, exist_ok=True)

        blob_prefix = "cv"
        blobs = storage.list_blobs(container_name="knowledgestore", prefix=blob_prefix)

        results = []
        for blob_name in blobs:
            file_name = os.path.basename(blob_name)
            download_path = os.path.join(download_dir, file_name)

            storage.get_file(
                container_name="knowledgestore",
                blob_name=blob_name,
                download_path=download_path
            )

            try:
                file_response = client.files.create(file=open(download_path, 'rb'), purpose="assistants")
                attach_response = client.vector_stores.files.create(
                    vector_store_id=vector_store["id"],
                    file_id=file_response.id
                )
                results.append({"file": file_name, "status": "success"})
            except Exception as e:
                print(f"Error with {file_name}: {str(e)}")
                results.append({"file": file_name, "status": "failed", "error": str(e)})

        return results
    except Exception as e:
        print(f"Error during file upload: {str(e)}")
        return {"status": "failed", "error": str(e)}
