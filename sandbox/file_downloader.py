import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage_account import AzureStorageAccount

def main():
    storage = AzureStorageAccount()
    download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".download")
    os.makedirs(download_dir, exist_ok=True)

    blob_prefix = "cv"
    blobs = storage.list_blobs(container_name="knowledgestore", prefix=blob_prefix)

    for blob_name in blobs:
        download_path = os.path.join(download_dir, os.path.basename(blob_name))
        storage.get_file(
            container_name="knowledgestore",
            blob_name=blob_name,
            download_path=download_path
        )

if __name__ == "__main__":
    main()
