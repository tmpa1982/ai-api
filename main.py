from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

key_vault_url = "https://tran-akv.vault.azure.net/"

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://tran-openai.openai.azure.com/",
    azure_ad_token_provider=token_provider,
)

models = client.models.list()
for model in models.data:
    print(f"Model ID: {model.id}")
