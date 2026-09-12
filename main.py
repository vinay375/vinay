from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from pytubefix import YouTube

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


def get_stream_type(stream) -> str:
    if stream.includes_audio_track and stream.includes_video_track:
        return "video_with_audio"

    if stream.includes_audio_track:
        return "audio_only"

    return "video_only"


@app.get("/api/video")
def get_video_links(
    url: str = Query(..., description="YouTube video URL"),
):
    if not is_youtube_url(url):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid YouTube URL.",
        )

    try:
        video = YouTube(url)

        # A single file containing both video and audio.
        progressive_streams = video.streams.filter(
            progressive=True,
            file_extension="mp4",
        )

        # MP4 video streams without audio.
        video_streams = video.streams.filter(
            adaptive=True,
            only_video=True,
            file_extension="mp4",
        )

        # Audio-only streams.
        audio_streams = video.streams.filter(
            only_audio=True,
        )

        streams = (
            list(progressive_streams)
            + list(video_streams)
            + list(audio_streams)
        )

        download_options = [
            {
                "itag": stream.itag,
                "type": get_stream_type(stream),
                "has_audio": stream.includes_audio_track,
                "has_video": stream.includes_video_track,
                "resolution": stream.resolution,
                "audio_bitrate": stream.abr,
                "mime_type": stream.mime_type,
                "file_size_bytes": stream.filesize,
                "download_url": stream.url,
            }
            for stream in streams
        ]

        return {
            "title": video.title,
            "video_id": video.video_id,
            "thumbnail_url": video.thumbnail_url,
            "download_options": download_options,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not get video links: {str(error)}",
        )
