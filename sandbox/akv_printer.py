import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from akv import AzureKeyVault

def main():
    akv = AzureKeyVault()
    secret_name = "openai-apikey"
    secret_value = akv.get_secret(secret_name)
    print(f"Secret '{secret_name}': {secret_value}")

if __name__ == "__main__":
    main()
