from voice_agent_tts import KokoroVoice

if __name__ == "__main__":
    text = "Hi Hai. how are you doing?"
    voice = KokoroVoice(voice="af_heart")
    voice.speak(text)