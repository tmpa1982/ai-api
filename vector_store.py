from openai import OpenAI
import os
import logging

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
                client.vector_stores.files.create(
                    vector_store_id=vector_store["id"],
                    file_id=file_response.id
                )
                results.append({"file": file_name, "status": "success"})
            except Exception as e:
                logging.error(f"Error with {file_name}: {str(e)}")
                results.append({"file": file_name, "status": "failed", "error": str(e)})

        return results
    except Exception as e:
        logging.error(f"Error during file upload: {str(e)}")
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
        logging.info("Vector store created: %s", details)
        return details
    except Exception as e:
        logging.error(f"Error creating vector store: {e}")
        return {}

def get_vector_store(store_name: str) -> dict:
    try:
        # Query existing vector stores
        vector_stores = client.vector_stores.list()
        for store in vector_stores:
            if store.name == store_name:
                details = {
                    "id": store.id,
                    "name": store.name,
                    "created_at": store.created_at,
                    "file_count": store.file_counts.completed
                }
                logging.info("Existing vector store found: %s", details)
                return details

        # If no existing store is found, create a new one
        return create_vector_store(store_name)
    except Exception as e:
        logging.error(f"Error retrieving or creating vector store: {e}")
        return {}

vector_store = get_vector_store("Knowledge Base")
