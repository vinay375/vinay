from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="YouTube Downloader API")

# Frontend se backend call enable karne ke liye CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/download")
async def download_video(url: str = Query(..., description="YouTube Video URL")):
    # Invidious / Public API node ka use IP blocking bypass karne ke liye
    api_url = f"https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "vQuality": "max",
        "isAudioOnly": False
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload, headers=headers, timeout=20.0)
            data = response.json()

            if response.status_code != 200 or data.get("status") == "error":
                raise HTTPException(status_code=400, detail="Video extract nahi ho pa rahi hai.")

            return {
                "status": "success",
                "download_url": data.get("url"),
                "filename": data.get("filename", "video.mp4")
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
