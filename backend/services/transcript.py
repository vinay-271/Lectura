from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptError(Exception):
    """Raised when a video's transcript cannot be retrieved."""


def get_transcript(video_id: str) -> str:
    api = YouTubeTranscriptApi()

    try:
        transcript = api.fetch(video_id)
    except Exception as exc:
        raise TranscriptError(
            f"Could not retrieve transcript for video: {video_id}"
        ) from exc

    return " ".join(snippet.text for snippet in transcript)