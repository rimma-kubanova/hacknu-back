from fastapi import APIRouter, UploadFile, Form, HTTPException
from typing import Optional
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
# nano banana -> image to image
HIGGSFIELD_URL="https://platform.higgsfield.ai"
HIGGSFIELD_API_KEY = os.getenv("HIGGSFIELD_API_KEY")

headers = {
    "Authorization": f"Bearer {HIGGSFIELD_API_KEY}",
    "Accept": "application/json",
}


@router.post("/mock/create")
async def generate_mock(
    images: UploadFile,
    prompt: str = Form(...),
    model: Optional[str] = Form(None)
    ):
    """
    Takes an image + prompt + optional model, sends to Higgsfield image-to-image API.
    """
    try:
        """
        "params": {
    "prompt": "dfbdfbdfbdbf",
    "aspect_ratio": "4:3",
    "input_images": [
      {
        "type": "image_url",
        "image_url": "https://d3snorpfx4xhv8.cloudfront.net/af3a4943-78d2-486b-a181-678bb1c8c168/45c5096c-4721-4a8f-8cff-bc862e5c0e70.png"
      }
    ]
  }"
  """
        files = []
        for image in images:
            files.append({"type": "image_url", "image_url": {image}})
        data = {"prompt": prompt}


        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{HIGGSFIELD_URL}/image-to-image",
                headers=headers,
                data=data,
                files=files
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock/image/create")
async def generate_stock_image(
    prompt: str = Form(...),
    image: Optional[UploadFile] = None
):
    """
    Generates stock image based on prompt, optionally guided by reference image.
    """
    try:
        files = None
        data = {"prompt": prompt}
        if image:
            files = {"image": (image.filename, await image.read(), image.content_type)}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{HIGGSFIELD_URL}/text-to-image",
                headers=headers,
                data=data,
                files=files
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3️⃣ TEXT/IMAGE-TO-STOCK-VIDEO
@router.post("/stock/video/create")
async def generate_stock_video(
    prompt: str = Form(...),
    image: Optional[UploadFile] = None
):
    """
    Generates a stock video based on a text prompt or reference image.
    """
    try:
        files = None
        data = {"prompt": prompt}
        if image:
            files = {"image": (image.filename, await image.read(), image.content_type)}

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{HIGGSFIELD_URL}/text-to-video",
                headers=headers,
                data=data,
                files=files
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))