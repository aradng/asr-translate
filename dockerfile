FROM python:3.9

WORKDIR /app

RUN apt update && apt install ffmpeg -y

RUN pip install --no-cache-dir fastapi
RUN pip install --no-cache-dir argostranslate
# Optional GPU support added in code
#RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir openai-whisper

RUN mkdir models

COPY asr-translate.py .

EXPOSE 8000

CMD ["fastapi", "run", "asr-translate.py", "--port", "8000"]
