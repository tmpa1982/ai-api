from azure.storage.blob import BlobServiceClient
from typing import Optional
from azure.identity import DefaultAzureCredential

class AzureStorageAccount:
    def __init__(self):
        account_url = "https://tranllm.blob.core.windows.net/"
        credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

    def get_file(self, container_name: str, blob_name: str, download_path: Optional[str] = None) -> bytes:
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_data = blob_client.download_blob().readall()
        if download_path:
            with open(download_path, "wb") as file:
                file.write(blob_data)
        return blob_data
