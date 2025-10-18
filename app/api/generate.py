from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import VideoGeneration
from app.schemas import (
    GenerationRequest, GenerationResponse, Asset, AssetMeta, 
    VideoHistoryResponse, VideoHistoryItem,
    MoodboardRequest, MoodboardResponse
)
from app.services.higgsfield import get_higgsfield_client
from app.database import get_db
import httpx
import asyncio
import random

router = APIRouter(prefix="/api", tags=["Generation"])


@router.post("/generate_image", response_model=GenerationResponse)
async def generate_image(
    request: GenerationRequest,
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


# Moodboard prompt templates
MOODBOARD_PROMPTS = [
    "Most Important: {PROMPT}. Also important: Flat, minimal hero key visual, bold geometric shapes, generous negative space, soft shadows, clean vector style, cohesive colorway, high contrast, no text, export-ready, centered composition.",
    "Most Important: {PROMPT}. Also important: Seamless repeating pattern inspired, flat vector motifs, simple modular geometry, subtle rhythm and scale variation, colorway, high legibility, edge-to-edge tiling, no text.",
    "Most Important: {PROMPT}. Also important: Color swatch collage showing large primary blocks and small accent chips, subtle paper/cutout feel (still flat), palette, balanced spacing, labels omitted (no text), clean grid.",
    "Most Important: {PROMPT}. Also important: Icon set sheet (12 icons) representing concepts, crisp 2px strokes, rounded joins, consistent corner radius, grid layout, flat vector, colorway, no labels or text, white background.",
    "Most Important: {PROMPT}. Also important: Abstract shape study using 3–5 geometric primitives, overlapping blends and soft shadows, flat vector look (no gradients or text), harmonious composition, palette , high contrast.",
    "Most Important: {PROMPT}. Also important: Sticker pack panel themed, 8–10 sticker illustrations with thick outline and flat fills, playful but minimal, even spacing, palette, white background, no text.",
    "Most Important: {PROMPT}. Also important: Minimal illustration vignette capturing the essence, single focal scene with 2–3 supporting elements, flat vector, subtle depth via layered shapes, colorway , no text.",
    "Most Important: {PROMPT}. Also important: UI card mood tile inspired, abstract cards and chips (no readable text), flat components, clear hierarchy by size/weight only, neutral background, palette, modern spacing.",
    "Most Important: {PROMPT}. Also important: Vector cutout collage, overlapping paper-like shapes and frames, soft shadows, torn-edge illusion (still flat), balanced asymmetry, palette, no text, tidy margins.",
    "Most Important: {PROMPT}. Also important: Wordmark exploration sheet expressed via abstract letterform shapes (no readable text), weight/curve experiments, 6–8 tiles on a grid, flat vector, palette, clean white background."
]

RANDOM_ASPECT_RATIOS = ["1:1", "9:16", "4:5", "3:4"]


async def _generate_single_image(client, prompt: str, aspect_ratio: str, input_images: list = None):
    try:
        input_imgs = []
        if input_images:
            input_imgs = [
                {"type": "image_url", "image_url": url}
                for url in input_images
            ]
        
        job = await client.text_to_image_nano(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            input_images=input_imgs
        )
        
        job_set_id = job["id"]
        results, _ = await client.wait_for_completion(job_set_id)
        
        image_url = results.get("raw", {}).get("url")
        return image_url if image_url else None
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None


@router.post("/generate_moodboard_videos", response_model=MoodboardResponse)
async def generate_moodboard_videos(
    request: MoodboardRequest,
):
    try:
        client = get_higgsfield_client()
        
        user_prompt = request.prompt if request.prompt else "modern design"
        
        final_prompts = [
            template.replace("{PROMPT}", user_prompt)
            for template in MOODBOARD_PROMPTS
        ]
        
        generated_images = []
        
        liked_count = len(request.liked_pictures) if request.liked_pictures else 0
        images_to_generate = 10 - liked_count
        
        if images_to_generate <= 0:
            return MoodboardResponse(
                images=request.liked_pictures[:10],
                total=len(request.liked_pictures[:10])
            )
        
        tasks = []
        
        for i in range(images_to_generate):
            prompt = final_prompts[i % len(final_prompts)]
            aspect_ratio = random.choice(RANDOM_ASPECT_RATIOS)
            
            input_images = request.liked_pictures if request.liked_pictures else None
            
            tasks.append(
                _generate_single_image(client, prompt, aspect_ratio, input_images)
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and isinstance(result, str):
                generated_images.append(result)
                
        return MoodboardResponse(
            images=generated_images,
            total=len(generated_images)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating moodboard: {str(e)}"
        )