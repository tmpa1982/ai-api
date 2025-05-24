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
