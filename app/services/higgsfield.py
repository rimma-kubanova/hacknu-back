import httpx
import asyncio
from typing import Optional, List, Dict, Any
from app.config import settings


class HiggsfieldClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or settings.HIGGSFIELD_API_KEY
        self.api_secret = api_secret or settings.HIGGSFIELD_API_SECRET
        self.base_url = base_url or settings.HIGGSFIELD_BASE_URL
        
        if not self.api_key or not self.api_secret:
            raise ValueError("HIGGSFIELD_API_KEY and HIGGSFIELD_API_SECRET must be set")
    
    def _headers(self) -> Dict[str, str]:
        return {
            "hf-api-key": self.api_key,
            "hf-secret": self.api_secret,
            "Content-Type": "application/json"
        }
    
    async def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_json(self, path: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def text_to_image_nano(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        input_images: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        input_images = input_images or []
        payload = {
            "params": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "input_images": input_images
            }
        }
        return await self.post_json("/text2image/nano-banana", payload)
    
    async def image_to_video_veo3(
        self,
        image_url: str,
        prompt: str,
        model: str = "veo-3-fast",
        enhance_prompt: bool = True
    ) -> Dict[str, Any]:
        payload = {
            "params": {
                "model": model,
                "prompt": prompt,
                "input_image": {
                    "type": "image_url",
                    "image_url": image_url
                },
                "enhance_prompt": enhance_prompt
            }
        }
        return await self.post_json("/image2video/veo3", payload)
    
    
    async def poll_job_set(self, job_set_id: str) -> Dict[str, Any]:
        return await self.get_json(f"/job-sets/{job_set_id}")
    
    async def wait_for_completion(
        self,
        job_set_id: str,
        max_wait: int = 1200,
        initial_delay: float = 1.2
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        delay = initial_delay
        waited = 0.0
        
        while waited < max_wait:
            job_set = await self.poll_job_set(job_set_id)
            
            if not job_set.get("jobs"):
                raise RuntimeError("No jobs found in job set")
            
            job = job_set["jobs"][0]
            status = job["status"]
            
            if status == "completed":
                return job["results"], job_set
            
            if status in ("failed", "error", "canceled"):
                error_msg = job.get("error_message", f"Job {status}")
                raise RuntimeError(f"Job failed: {error_msg}")
            
            await asyncio.sleep(delay)
            waited += delay
            delay = min(2.0, delay + 0.3)
        
        raise TimeoutError(f"Generation timed out after {max_wait}s")


_client: Optional[HiggsfieldClient] = None


def get_higgsfield_client() -> HiggsfieldClient:
    global _client
    if _client is None:
        _client = HiggsfieldClient()
    return _client

