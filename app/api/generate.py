from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.models import User
from app.schemas import GenerationRequest, GenerationResponse, Asset, AssetMeta
from app.services.higgsfield import get_higgsfield_client
import httpx

router = APIRouter(prefix="/api", tags=["Generation"])


@router.post("/mock_create", response_model=GenerationResponse)
async def mock_create(
    request: GenerationRequest
):
    """
    Create mockup using Text-to-Image (Nano Banana).
    Optionally animates result with Image-to-Video if options.animate=true.
    
    Use cases:
    - Device mockup (laptop/mobile)
    - Billboard/poster placement
    - UX design showcase
    """
    try:
        client = get_higgsfield_client()
        
        # Prepare input images for Higgsfield
        input_images = []
        if request.images:
            input_images = [
                {"type": "image_url", "image_url": url}
                for url in request.images
            ]
        
        # Step 1: Text-to-Image with Nano Banana
        job = await client.text_to_image_nano(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            input_images=input_images
        )
        
        job_set_id = job["id"]
        results, job_set = await client.wait_for_completion(job_set_id)
        
        # Extract image URL
        image_url = results.get("raw", {}).get("url")
        if not image_url:
            raise HTTPException(status_code=500, detail="No image URL in response")
        
        assets = [
            Asset(
                kind="image",
                url=image_url,
                meta=AssetMeta(type="image")
            )
        ]
        
        # Step 2: Optional animation with Image-to-Video
        if request.options and request.options.animate:
            model = "veo-3-polish" if request.options.model_hint == "polish" else "veo-3-fast"
            animation_prompt = request.options.mode or "subtle parallax pan, cinematic lighting, 8s"
            
            i2v_job = await client.image_to_video_veo3(
                image_url=image_url,
                prompt=animation_prompt,
                model=model,
                enhance_prompt=True
            )
            
            vid_job_id = i2v_job["id"]
            vid_results, _ = await client.wait_for_completion(vid_job_id)
            
            video_url = vid_results.get("raw", {}).get("url")
            if video_url:
                assets.append(
                    Asset(
                        kind="video",
                        url=video_url,
                        meta=AssetMeta(type="video", dur=8)
                    )
                )
        
        return GenerationResponse(
            status="completed",
            assets=assets,
            job_set_id=job_set_id,
            provider="higgsfield",
            input_echo={
                "prompt": request.prompt,
                "images": request.images,
                "aspect_ratio": request.aspect_ratio
            }
        )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Higgsfield API error: {str(e)}"
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/stock_image", response_model=GenerationResponse)
async def stock_image(
    request: GenerationRequest
):
    """
    Generate brand-safe stock images using Text-to-Image (Nano Banana).
    
    Supports optional reference images for style guidance.
    """
    try:
        client = get_higgsfield_client()
        
        # Prepare input images
        input_images = []
        if request.images:
            input_images = [
                {"type": "image_url", "image_url": url}
                for url in request.images
            ]
        
        # Generate image
        job = await client.text_to_image_nano(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            input_images=input_images
        )
        
        job_set_id = job["id"]
        results, _ = await client.wait_for_completion(job_set_id)
        
        image_url = results.get("raw", {}).get("url")
        if not image_url:
            raise HTTPException(status_code=500, detail="No image URL in response")
        
        return GenerationResponse(
            status="completed",
            assets=[
                Asset(
                    kind="image",
                    url=image_url,
                    meta=AssetMeta(type="image")
                )
            ],
            job_set_id=job_set_id,
            provider="higgsfield",
            input_echo={
                "prompt": request.prompt,
                "aspect_ratio": request.aspect_ratio
            }
        )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Higgsfield API error: {str(e)}"
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/stock_video", response_model=GenerationResponse)
async def stock_video(
    request: GenerationRequest
):
    """
    Generate stock video.
    - If images provided: Image-to-Video (Veo 3)
    - If no images: Text-to-Video (Kling 2.1 Master)
    """
    try:
        client = get_higgsfield_client()

        # Image-to-Video flow
        model = "veo-3-polish" if request.options and request.options.model_hint == "polish" else "veo-3-fast"
        
        job = await client.image_to_video_veo3(
            image_url=request.images[0],
            prompt=request.prompt,
            model=model,
            enhance_prompt=True
        )
        
        job_set_id = job["id"]
        results, _ = await client.wait_for_completion(job_set_id, max_wait=180)
        
        video_url = results.get("raw", {}).get("url")
        if not video_url:
            raise HTTPException(status_code=500, detail="No video URL in response")
        
        duration = request.options.duration if request.options else 8
        
        return GenerationResponse(
            status="completed",
            assets=[
                Asset(
                    kind="video",
                    url=video_url,
                    meta=AssetMeta(
                        type="video",
                        dur=duration,
                        aspect=request.aspect_ratio
                    )
                )
            ],
            job_set_id=job_set_id,
            provider="higgsfield",
            input_echo={
                "prompt": request.prompt,
                "aspect_ratio": request.aspect_ratio
            }
        )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Higgsfield API error: {str(e)}"
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

