import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage_account import AzureStorageAccount

def main():
    storage = AzureStorageAccount()
    storage.get_file(
        container_name="knowledgestore",
        blob_name="cv/Jia Yu Lee_CV.pdf",
        download_path="cv.pdf"
    )

if __name__ == "__main__":
    main()
