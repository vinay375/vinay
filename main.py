from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Query
import yt_dlp

app = FastAPI(title="YouTube Link API")


def is_youtube_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }


@app.get("/api/video")
def get_video_links(url: str = Query(..., description="YouTube video URL")):
    if not is_youtube_url(url):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid YouTube URL.",
        )

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # Render/Cloud IP ban se bachne ke liye user-agent/extractor args
        'extractor_args': {'youtube': ['player_client=android,web']},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            download_options = []
            for stream in info.get("formats", []):
                # Streams filters
                vcodec = stream.get("vcodec")
                acodec = stream.get("acodec")
                
                has_video = vcodec != "none" and vcodec is not None
                has_audio = acodec != "none" and acodec is not None

                if has_video and has_audio:
                    stream_type = "video_with_audio"
                elif has_audio:
                    stream_type = "audio_only"
                elif has_video:
                    stream_type = "video_only"
                else:
                    continue

                download_options.append({
                    "format_id": stream.get("format_id"),
                    "type": stream_type,
                    "has_audio": has_audio,
                    "has_video": has_video,
                    "resolution": stream.get("resolution") or f"{stream.get('height')}p",
                    "audio_bitrate": f"{int(stream.get('abr'))}kbps" if stream.get('abr') else None,
                    "mime_type": stream.get("ext"),
                    "file_size_bytes": stream.get("filesize") or stream.get("filesize_approx"),
                    "download_url": stream.get("url"),
                })

            return {
                "title": info.get("title"),
                "video_id": info.get("id"),
                "thumbnail_url": info.get("thumbnail"),
                "download_options": download_options,
            }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not get video links: {str(error)}",
        )
