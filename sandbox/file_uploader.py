import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage_account import AzureStorageAccount

def main():
    storage = AzureStorageAccount()
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".upload")

    blob_prefix = "cv"
    container_name = "knowledgestore"

    if not os.path.exists(upload_dir):
        print(f"Upload directory {upload_dir} does not exist")
        return

    for root, _, files in os.walk(upload_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            # Build blob name: prefix + relative path inside upload_dir
            rel_path = os.path.relpath(file_path, upload_dir).replace("\\", "/")
            blob_name = f"{blob_prefix}/{rel_path}"

            with open(file_path, "rb") as f:
                data = f.read()

            print(f"Uploading {file_path} → {container_name}/{blob_name}")
            storage.upload_file(container_name, blob_name, data)

if __name__ == "__main__":
    main()
