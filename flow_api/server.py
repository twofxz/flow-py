"""
FastAPI Server - Emula o endpoint da OpenAI `POST /v1/images/generations` para integração total.
"""

import os
import base64
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .client import FlowClient
from .editor import FlowEditor
from .downloader import FlowDownloader

app = FastAPI(
    title="Google Flow API (OpenAI Compatible)",
    description="Local server translating OpenAI /v1/images/generations requests to Google Flow",
    version="0.1.0"
)

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = "Nano Banana 2"
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024" # 1024x1024 -> 1:1, 1792x1024 -> 16:9, 1024x1792 -> 9:16
    response_format: Optional[str] = "url" # "url" or "b64_json"

class ImageItem(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageItem]

client_instance: Optional[FlowClient] = None

@app.on_event("startup")
def startup_event():
    global client_instance
    client_instance = FlowClient()
    client_instance.connect()

@app.on_event("shutdown")
def shutdown_event():
    global client_instance
    if client_instance:
        client_instance.close()

def size_to_ratio(size: str) -> str:
    if "1792x1024" in size or "16:9" in size:
        return "16:9"
    elif "1024x1792" in size or "9:16" in size:
        return "9:16"
    return "1:1"

@app.post("/v1/images/generations", response_model=ImageGenerationResponse)
def generate_images(req: ImageGenerationRequest):
    import time
    global client_instance
    if not client_instance or not client_instance.page:
        raise HTTPException(status_code=500, detail="Flow client not connected")

    ratio = size_to_ratio(req.size or "1024x1024")
    client_instance.ensure_canvas()
    editor = FlowEditor(client_instance.page)
    downloader = FlowDownloader(client_instance.page, client_instance.download_dir)

    editor.submit_prompt(req.prompt, model=req.model or "Nano Banana 2", aspect_ratio=ratio)
    success = editor.wait_for_generation(timeout=90)
    if not success:
        raise HTTPException(status_code=504, detail="Generation timeout on Google Flow")

    saved_path = downloader.download_current(resolution="1K")
    if not saved_path:
        raise HTTPException(status_code=500, detail="Failed to retrieve downloaded image")

    if req.response_format == "b64_json":
        with open(saved_path, "rb") as img_f:
            b64 = base64.b64encode(img_f.read()).decode("utf-8")
        data = [ImageItem(b64_json=b64)]
    else:
        data = [ImageItem(url=f"file://{os.path.abspath(saved_path)}")]

    return ImageGenerationResponse(created=int(time.time()), data=data)
