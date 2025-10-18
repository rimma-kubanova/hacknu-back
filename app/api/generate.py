from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import VideoGeneration
from app.schemas import (
    GenerationRequest, GenerationResponse, Asset, AssetMeta, 
    VideoHistoryResponse, VideoHistoryItem,
    MoodboardRequest, MoodboardResponse, VideoDetailResponse
)
from app.services.higgsfield import get_higgsfield_client
from app.database import get_db
from app.config import settings
import httpx
import asyncio
import random

router = APIRouter(prefix="/api", tags=["Generation"])


def get_openai_client():
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


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
        db.refresh(video_gen)
                
        return GenerationResponse(
            status="completed",
            assets=[
                Asset(
                    kind="video",
                    url=video_url,
                    video_id=video_gen.id,
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


@router.post("/generate_fake_video", response_model=GenerationResponse)
async def generate_fake_video():
    return GenerationResponse(
        status="completed",
        assets=[
            Asset(
                kind="video",
                video_id=1, 
                url="https://d3u0tzju9qaucj.cloudfront.net/5529083c-d5ae-418a-8265-5e779de64095/7e65acb4-d2b2-4785-bd75-d81f06303389.mp4",
                meta=AssetMeta(
                    type="video",
                )
            )
        ],
        provider="higgsfield",
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


@router.get("/videos/{video_id}", response_model=VideoDetailResponse)
async def get_video_by_id(video_id: int, db: Session = Depends(get_db)):
    video = db.query(VideoGeneration).filter(
        VideoGeneration.id == video_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoDetailResponse(
        id=video.id,
        video_url=video.video_url,
        prompt=video.prompt,
        aspect_ratio=video.aspect_ratio,
        job_set_id=video.job_set_id,
        created_at=video.created_at.isoformat()
    )


RANDOM_ASPECT_RATIOS = ["1:1", "9:16", "4:5", "3:4"]


async def generate_moodboard_prompts_with_openai(user_prompt: str, count: int) -> list[str]:
    openai_client = get_openai_client()
    
    system_prompt = """You are an expert art director creating diverse, high-quality image prompts for a moodboard.
Generate {count} unique, detailed image prompts based on the user's theme.

Requirements for each prompt:
- Be specific and descriptive
- Include artistic style, lighting, composition details
- Vary perspectives and moods across prompts
- Make them realistic, cinematic, and high-quality
- Include technical photography/rendering details
- Each prompt should explore different aspects of the theme
- NO text, watermarks, or words in the images
- Each prompt should be 50-100 words

Styles to vary across:
- Photorealistic photography (natural light, depth of field)
- Cinematic film stills (35mm, color grading)
- 3D renders (materials, studio lighting)
- Minimalist compositions
- Editorial style
- Product photography
- Architectural perspectives
- Nature close-ups
- Abstract interpretations
- Atmospheric mood pieces

Return ONLY a JSON array of {count} prompt strings, nothing else."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt.replace("{count}", str(count))},
                {"role": "user", "content": f"Theme: {user_prompt}\n\nGenerate {count} diverse, professional image prompts for a moodboard exploring this theme from different angles and styles."}
            ],
            temperature=0.9,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        if isinstance(result, dict):
            prompts = result.get("prompts", list(result.values()))
        else:
            prompts = result
            
        return prompts[:count]
    
    except Exception as e:
        print(f"OpenAI error: {str(e)}")
        return [f"{user_prompt}, professional photography, high quality, detailed" for _ in range(count)]


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


@router.post("/generate_moodboard_images", response_model=MoodboardResponse)
async def generate_moodboard_images(
    request: MoodboardRequest,
):
    try:
        client = get_higgsfield_client()
        
        user_prompt = request.prompt if request.prompt else "modern design aesthetic"
        
        liked_count = len(request.liked_pictures) if request.liked_pictures else 0
        images_to_generate = 10 - liked_count
        
        if images_to_generate <= 0:
            return MoodboardResponse(
                images=request.liked_pictures[:10],
                total=len(request.liked_pictures[:10])
            )
        
        ai_prompts = await generate_moodboard_prompts_with_openai(user_prompt, images_to_generate)

        generated_images = []
        tasks = []
        
        for _, prompt in enumerate(ai_prompts):
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