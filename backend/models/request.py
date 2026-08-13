from pydantic import BaseModel, HttpUrl


class GenerateNotesRequest(BaseModel):
    youtube_url: HttpUrl