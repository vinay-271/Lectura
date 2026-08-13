from fastapi import FastAPI

from models.request import GenerateNotesRequest

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/generate-notes")
def generate_notes(request: GenerateNotesRequest):
    return {
        "message": "Hello from Lectura Backend",
        "youtube_url": request.youtube_url
    }