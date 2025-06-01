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

## Voice Assistant Usage

The application includes a voice-based chat interface that allows you to speak with the AI assistant. The voice assistant uses Azure OpenAI services for speech-to-text and text-to-speech capabilities.

1. Start the server:
   ```
   python main.py
   ```

2. In a new terminal, launch the voice client:
   ```
   python sandbox\voice_client.py
   ```

3. Using the voice interface:
   - Press Enter when prompted to start recording your message
   - Speak your question or prompt clearly
   - Press Enter again to stop recording
   - Wait for the AI assistant's voice response to play
   - The assistant will respond both with voice and display status messages

4. To exit:
   - Type 'exit' when prompted to start a new recording
   - Or close either terminal window

Note: Ensure your microphone is properly configured and your system's audio input/output devices are working correctly. The default sample rate is 44.1kHz but will adjust to your system's default input device.