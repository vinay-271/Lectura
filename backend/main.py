from fastapi import FastAPI

from models.request import GenerateNotesRequest

from utils.youtube import extract_video_id

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/generate-notes")
def generate_notes(request: GenerateNotesRequest):
    video_id = extract_video_id(str(request.youtube_url))

    return {
        "message": "Hello from Lectura Backend",
        "youtube_url": str(request.youtube_url),
        "video_id": video_id
    }