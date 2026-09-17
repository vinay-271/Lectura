"""Frame extraction, resizing, compression and optimization.

``FrameExtractor`` turns selected video frames into optimized image
files on disk. Resizing happens with ``INTER_AREA`` (the correct
interpolation for downscaling) and the aspect ratio is preserved, so
screenshots from any video resolution come out clean and small.
"""

from __future__ import annotations

import re
from pathlib import Path

import cv2
import numpy as np

from .models import ExtractedFrame

# Characters that are unsafe or confusing inside filenames on disk.
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_timestamp_label(timestamp: float) -> str:
    """Turn a timestamp into a stable, filesystem-safe label.

    Negative timestamps are clamped to zero so paths never start with
    something like ``frame_-1.20.jpg``.
    """
    safe_timestamp = max(0.0, float(timestamp))
    label = f"{safe_timestamp:.2f}"
    return _UNSAFE_FILENAME_CHARS.sub("_", label)


class FrameExtractor:
    """Saves selected frames as resized, compressed image files."""

    def __init__(
        self,
        output_dir: str = "temp/frames",
        jpeg_quality: int = 85,
        max_width: int = 1280,
        max_height: int = 720,
    ):
        """Create an extractor.

        Args:
            output_dir: Directory where extracted images are written.
            jpeg_quality: JPEG quality (1-100) used for .jpg/.jpeg output.
            max_width: Screenshots wider than this are downscaled to fit.
            max_height: Screenshots taller than this are downscaled to fit.
        """
        if not 1 <= jpeg_quality <= 100:
            raise ValueError("jpeg_quality must be between 1 and 100")
        if max_width < 1 or max_height < 1:
            raise ValueError("max dimensions must be at least 1x1")

        self.output_dir = Path(output_dir)
        self.jpeg_quality = jpeg_quality
        self.max_width = max_width
        self.max_height = max_height

    def resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Downscale a frame to fit inside the configured bounds.

        The aspect ratio is preserved and frames already within the
        bounds are returned unchanged (no needless quality loss).
        """
        height, width = frame.shape[:2]

        if width <= self.max_width and height <= self.max_height:
            return frame

        scale = min(
            self.max_width / width,
            self.max_height / height,
        )
        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))

        return cv2.resize(
            frame,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )

    def _encode(
        self,
        frame: np.ndarray,
        extension: str,
    ) -> bytes:
        """Encode a frame to bytes using settings for the extension."""
        normalized_extension = extension.lower()

        if normalized_extension in (".jpg", ".jpeg"):
            params = [
                int(cv2.IMWRITE_JPEG_QUALITY),
                int(self.jpeg_quality),
                int(cv2.IMWRITE_JPEG_OPTIMIZE),
                1,
            ]
        elif normalized_extension == ".png":
            params = [int(cv2.IMWRITE_PNG_COMPRESSION), 6]
        else:
            raise ValueError(
                f"Unsupported image format: {extension!r}"
            )

        success, buffer = cv2.imencode(normalized_extension, frame, params)
        if not success:
            raise ValueError(
                f"Unable to encode frame as {normalized_extension}"
            )

        return bytes(buffer)

    def save_frame(
        self,
        frame: np.ndarray,
        timestamp: float,
        image_format: str = ".jpg",
    ) -> ExtractedFrame:
        """Resize, compress and save a frame; return its metadata.

        Args:
            frame: BGR image (as produced by OpenCV).
            timestamp: Time of the frame inside the video, in seconds.
            image_format: Output format (``.jpg``/``.jpeg``/``.png``).

        Raises:
            TypeError: If ``frame`` is not a valid image array.
        """
        if not isinstance(frame, np.ndarray) or frame.ndim < 2:
            raise TypeError(
                "frame must be a non-empty OpenCV image (numpy array)"
            )

        # Make sure the output directory exists before writing anything.
        self.output_dir.mkdir(parents=True, exist_ok=True)

        resized_frame = self.resize_frame(frame)
        encoded_bytes = self._encode(resized_frame, image_format)

        image_path = self.output_dir / (
            f"frame_{_sanitize_timestamp_label(timestamp)}"
            f"{image_format.lower()}"
        )

        # Avoid silently overwriting when two frames share a timestamp
        # (e.g. the same run on the same video, or zero-duration videos).
        unique_path = image_path
        counter = 1
        while unique_path.exists():
            unique_path = image_path.with_name(
                f"{image_path.stem}_{counter}{image_path.suffix}"
            )
            counter += 1

        unique_path.write_bytes(encoded_bytes)

        height, width = resized_frame.shape[:2]

        return ExtractedFrame(
            timestamp=float(timestamp),
            image_path=str(unique_path),
            width=int(width),
            height=int(height),
            file_size_bytes=len(encoded_bytes),
        )
