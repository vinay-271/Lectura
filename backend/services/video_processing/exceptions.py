"""Exceptions for the video-processing module.

``VideoProcessingError`` is the single base type the API layer (Member 1)
can catch to map any video-processing failure to an HTTP error, mirroring
the ``TranscriptError`` convention used by ``services/transcript.py``.
"""

class VideoProcessingError(Exception):
    """Raised when a video cannot be validated, opened or processed."""


class VideoNotFoundError(VideoProcessingError, FileNotFoundError):
    """Raised when the video file does not exist on disk.

    Also subclasses ``FileNotFoundError`` so existing ``except
    FileNotFoundError`` handlers (and HTTP 404 mapping) keep working.
    """


class InvalidVideoError(VideoProcessingError, ValueError):
    """Raised when the file exists but is not a usable video.

    Also subclasses ``ValueError`` so existing ``except ValueError``
    handlers (and HTTP 400/422 mapping) keep working.
    """
