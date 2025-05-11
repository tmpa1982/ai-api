from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from fastapi import FastAPI

key_vault_url = "https://tran-akv.vault.azure.net/"

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://tran-openai.openai.azure.com/",
    azure_ad_token_provider=token_provider,
)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/models")
async def list_models():
    return client.models.list().data

@app.post("/question")
async def ask_question():
    return client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that talks in piraty style.",
            },
            {
                "role": "user",
                "content": "I am going to Paris, what should I see?",
            }
        ],
        model="gpt-4o-mini"
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
