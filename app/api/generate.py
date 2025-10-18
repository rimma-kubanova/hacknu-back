from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.models import User, VideoGeneration
from app.schemas import GenerationRequest, GenerationResponse, Asset, AssetMeta, VideoHistoryResponse, VideoHistoryItem
from app.services.higgsfield import get_higgsfield_client
from app.database import get_db
import httpx

router = APIRouter(prefix="/api", tags=["Generation"])


@router.post("/generate_image", response_model=GenerationResponse)
async def generate_image(
    request: GenerationRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        client = get_higgsfield_client()
        
        input_images = []
        if request.images:
            input_images = [
                {"type": "image_url", "image_url": url}
                for url in request.images
            ]
        
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


@router.post("/generate_video", response_model=GenerationResponse)
async def generate_video(
    request: GenerationRequest,
    db: Session = Depends(get_db)
):
    try:
        client = get_higgsfield_client()

        model = "veo-3-fast"
        
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
        
        video_gen = VideoGeneration(
            video_url=video_url,
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            job_set_id=job_set_id
        )
        db.add(video_gen)
        db.commit()
                
        return GenerationResponse(
            status="completed",
            assets=[
                Asset(
                    kind="video",
                    url=video_url,
                    meta=AssetMeta(
                        type="video",
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


@router.get("/videos", response_model=VideoHistoryResponse)
async def get_all_videos(db: Session = Depends(get_db)):
    videos = db.query(VideoGeneration).order_by(
        VideoGeneration.created_at.desc()
    ).all()
    
    video_items = [
        VideoHistoryItem(
            id=v.id,
            video_url=v.video_url,
            prompt=v.prompt,
            aspect_ratio=v.aspect_ratio,
            job_set_id=v.job_set_id,
            created_at=v.created_at.isoformat()
        )
        for v in videos
    ]
    
    return VideoHistoryResponse(
        total=len(video_items),
        videos=video_items
    )