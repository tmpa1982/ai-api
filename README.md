# Overview

Lists available model IDs from the deployed Azure OpenAI service

# How to use

On Windows

## Setup

```
az login
.\venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Run API server

```
uvicorn main:app
```

## Run sandbox tools

```
python sandbox\akv_printer.py
python sandbox\file_downloader.py
```

# Debug

## Azure OpenID verification

```
https://login.microsoftonline.com/<TENANT_ID>/v2.0/.well-known/openid-configuration
```

Example:

```
https://login.microsoftonline.com/aa76d384-6e66-4f99-acef-1264b8cef053/v2.0/.well-known/openid-configuration


For audio functinality using Kokoro install brew install portaudio

```
