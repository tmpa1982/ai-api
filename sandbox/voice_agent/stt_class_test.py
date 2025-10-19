from RealtimeSTT import AudioToTextRecorder


if __name__ == '__main__':
    recorder = AudioToTextRecorder(
    model="tiny",
    device='cpu',
    post_speech_silence_duration=1.0,
    )
    recorder.start()
    input("Press Enter to stop recording...")
    recorder.stop()
    print("Transcription: ", recorder.text())