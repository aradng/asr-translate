from fastapi import FastAPI, UploadFile, File, HTTPException
import argostranslate.package
import argostranslate.translate
import whisper
import torch
import uuid
import os
import asyncio
import logging
from sys import stdout

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
consoleHandler = logging.StreamHandler(stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

app = FastAPI()

from_code = os.getenv("translate_from", "en")
to_code = os.getenv("translate_to", "fa")
model_name = os.getenv("model", "base")
n_asr_workers = int(os.getenv("n_asr_workers", 3))
n_translate_workers = int(os.getenv("n_translate_workers", 3))

argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    )
)
argostranslate.package.install_from_path(package_to_install.download())

results = {}

@app.post("/", status_code=202)
async def fetch(file: UploadFile = File(..., media_type="audio/wav")) -> dict:
    if file.content_type != "audio/wav":
        raise HTTPException(status_code=415, detail="Unsupported Media Type")
    id = str(uuid.uuid4())
    await app.asr_queue.put({"file": await file.read(), "id": id})
    results[id] = None
    return {"id": id}


@app.get("/")
async def result(id):
    if id not in results.keys():
        raise HTTPException(status_code=404, detail="ID Not Found")
    if results[id] is None:
        return {"status": "Processing"}
    res = results.pop(id)
    return {"translation": res}


async def asr(name):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device, download_root="./models")
    logger.info(f"{name} started")
    while True:
        item = await app.asr_queue.get()
        logger.debug(f'{name} assigned task with id: {item["id"]}')
        contents = item["file"]
        fn = f'{item["id"]}.wav'
        try:
            with open(fn, "wb") as file:
                file.write(contents)
            result = model.transcribe(fn)
            await app.translate_queue.put({"text": result["text"], "id": item["id"]})

        finally:
            os.remove(fn)
            app.asr_queue.task_done()
            logger.debug(
                f"{name} finished task with id {item['id']} with result:\n{result['text']}"
            )


async def translate(name):
    logger.info(f"{name} started")
    while True:
        item = await app.translate_queue.get()
        logger.debug(f'{name} assigned task with id: {item["id"]}')
        translatedText = argostranslate.translate.translate(
            item["text"], from_code, to_code
        )
        results[item["id"]] = translatedText
        app.translate_queue.task_done()
        logger.debug(
            f"{name} finished task with id {item['id']} with result:\n{translatedText}"
        )


@app.on_event("startup")
async def star_workers():
    app.asr_queue = asyncio.Queue()
    app.translate_queue = asyncio.Queue()
    asr_workers = [
        asyncio.create_task(asr(f"asr-worker-{_}")) for _ in range(n_asr_workers)
    ]
    translate_workers = [
        asyncio.create_task(translate(f"translate-worker-{_}"))
        for _ in range(n_translate_workers)
    ]
