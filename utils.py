from openai import OpenAI

from akv import AzureKeyVault
from storage_account import AzureStorageAccount

akv = AzureKeyVault()
openai_key = akv.get_secret("openai-apikey")
client = OpenAI(api_key=openai_key)

storage = AzureStorageAccount()

def upload_file():
    file_name = "Jia Yu Lee_CV.pdf"
    file_path = "cv.pdf"
    try:
        storage.get_file(
            container_name="knowledgestore",
            blob_name=f"cv/{file_name}",
            download_path=file_path
        )

        file_response = client.files.create(file=open(file_path, 'rb'), purpose="assistants")
        attach_response = client.vector_stores.files.create(
            vector_store_id=vector_store["id"],
            file_id=file_response.id
        )
        return {"file": file_name, "status": "success"}
    except Exception as e:
        print(f"Error with {file_name}: {str(e)}")
        return {"file": file_name, "status": "failed", "error": str(e)}

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
