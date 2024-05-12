# ASR + Translator as Microservice
Automatic Speech Recognition (ASR) is a software that can transcribe human speech.

In this project you have to implement an ASR system plus a text translator in microservice architecture. The input voice file is guaranteed to be in English and the output text must be in Persian

Your system exposes two API endpoints:
1. POST: accepts a voice file (wav), returns 202 status code and begins the transcription and the translation in the background.
2. GET: outputs the Persian transcription of the voice file received in the first endpoint if the processing was finished. Otherwise, it informs the client that the processing is still undergoing.
For abstraction, you don't need to implement authentication. Also, it's guaranteed that only one file is being fed to the system at a time so we won't have to manage file/task IDs.

Your microservice architecture should be designed in a way to minimize the processing latency as it scales horizontally.

You should publish the codebase on a GitHub repository (private or public) and share it to us.

Technologies that might help you with ASR/translation:
1. VOSK or Whisper
2. Argostranslate
