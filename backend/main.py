from fastapi import FastAPI

from models.request import GenerateNotesRequest

from utils.youtube import extract_video_id

from services.transcript import get_transcript

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/generate-notes")
def generate_notes(request: GenerateNotesRequest):
    video_id = extract_video_id(str(request.youtube_url))

    transcript = get_transcript(video_id)

    return {
        "message": "Transcript retrieved successfully",
        "youtube_url": str(request.youtube_url),
        "video_id": video_id,
        "transcript": transcript
    }