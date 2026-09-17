"""Unit tests for ``FrameExtractor``."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from services.video_processing import ExtractedFrame, FrameExtractor


@pytest.fixture
def extractor(tmp_path: Path) -> FrameExtractor:
    return FrameExtractor(output_dir=str(tmp_path / "frames"))


class TestSaving:
    def test_save_creates_output_dir_and_file(self, extractor, tmp_path):
        frame = np.full((360, 640, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=1.5)

        assert isinstance(saved, ExtractedFrame)
        image_path = Path(saved.image_path)
        assert image_path.parent == tmp_path / "frames"
        assert image_path.exists()

    def test_saved_image_decodes_with_correct_size(
        self, extractor, tmp_path
    ):
        frame = np.full((360, 640, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=2.0)
        decoded = cv2.imread(saved.image_path)

        assert decoded is not None
        assert decoded.shape[:2] == (360, 640)

    def test_large_frames_are_downscaled(self, extractor):
        frame = np.full((1080, 1920, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=1.0)

        assert saved.width == 1280
        assert saved.height == 720

    def test_small_frames_are_not_upscaled(self, extractor):
        frame = np.full((72, 128, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=1.0)

        assert saved.width == 128
        assert saved.height == 72

    def test_portrait_frames_keep_aspect_ratio(self, extractor):
        frame = np.full((1920, 1080, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=1.0)

        # 1080 wide x 1920 tall fit into 1280x720 bounds -> 480x853
        # (720 * 1080/1920 = 405 wide, 720 tall) -- check exact values:
        # scale = min(1280/1080, 720/1920) = 0.375 -> 405x720.
        assert saved.width == 405
        assert saved.height == 720

        # Aspect ratio is preserved (within 1px rounding).
        ratio_before = 1080 / 1920
        ratio_after = saved.width / saved.height
        assert ratio_after == pytest.approx(ratio_before, rel=0.01)

    def test_negative_timestamp_is_sanitized(self, extractor):
        frame = np.full((72, 128, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=-1.25)

        assert "frame_0.00" in saved.image_path
        assert Path(saved.image_path).exists()

    def test_same_timestamp_does_not_overwrite(self, extractor):
        frame = np.full((72, 128, 3), 120, dtype=np.uint8)

        first = extractor.save_frame(frame, timestamp=1.0)
        second = extractor.save_frame(frame, timestamp=1.0)

        assert first.image_path != second.image_path
        assert Path(first.image_path).exists()
        assert Path(second.image_path).exists()

    def test_png_output_is_supported(self, extractor):
        frame = np.full((72, 128, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=1.0, image_format=".png")

        assert saved.image_path.endswith(".png")
        assert Path(saved.image_path).exists()

    def test_unsupported_format_raises(self, extractor):
        frame = np.full((72, 128, 3), 120, dtype=np.uint8)

        with pytest.raises(ValueError, match="Unsupported image format"):
            extractor.save_frame(frame, timestamp=1.0, image_format=".bmp")

    def test_invalid_frame_type_raises(self, extractor):
        with pytest.raises(TypeError):
            extractor.save_frame("not an image", timestamp=1.0)

    def test_metadata_is_reported(self, extractor, tmp_path):
        frame = np.full((1080, 1920, 3), 120, dtype=np.uint8)

        saved = extractor.save_frame(frame, timestamp=3.5)

        assert saved.timestamp == pytest.approx(3.5)
        assert saved.file_size_bytes == Path(saved.image_path).stat().st_size
        assert saved.filename == Path(saved.image_path).name


class TestConfiguration:
    def test_invalid_jpeg_quality_raises(self, tmp_path):
        with pytest.raises(ValueError):
            FrameExtractor(output_dir=str(tmp_path), jpeg_quality=0)
        with pytest.raises(ValueError):
            FrameExtractor(output_dir=str(tmp_path), jpeg_quality=101)

    def test_invalid_max_dimensions_raise(self, tmp_path):
        with pytest.raises(ValueError):
            FrameExtractor(output_dir=str(tmp_path), max_width=0)
        with pytest.raises(ValueError):
            FrameExtractor(output_dir=str(tmp_path), max_height=0)

    def test_higher_quality_produces_larger_files(self, tmp_path):
        # Use a colorful gradient so JPEG output size actually reacts to
        # quality; a flat color compresses to nearly nothing either way.
        gradient = np.tile(
            np.arange(0, 256, dtype=np.uint8), (720, 640)
        )
        frame = cv2.merge(
            [gradient, np.fliplr(gradient).copy(), 255 - gradient]
        )
        low_quality = FrameExtractor(
            output_dir=str(tmp_path / "low"), jpeg_quality=40
        )
        high_quality = FrameExtractor(
            output_dir=str(tmp_path / "high"), jpeg_quality=95
        )

        low = low_quality.save_frame(frame, timestamp=1.0)
        high = high_quality.save_frame(frame, timestamp=1.0)

        assert high.file_size_bytes > low.file_size_bytes
