from pydantic import BaseModel, HttpUrl, field_validator

from utils.youtube import is_youtube_url


class GenerateNotesRequest(BaseModel):
    youtube_url: HttpUrl

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, value: HttpUrl) -> HttpUrl:
        if not is_youtube_url(str(value)):
            raise ValueError("URL must be a YouTube URL")

        return value