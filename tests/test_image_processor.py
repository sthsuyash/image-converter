import pytest
from unittest.mock import Mock, patch, MagicMock
import io
from PIL import Image

from core.image_processor import ImageProcessor
from utils.exceptions import ImageProcessingError


class TestImageProcessor:

    @pytest.fixture
    def processor(self):
        with patch("core.image_processor.Logger"):
            return ImageProcessor()

    def test_is_supported_image(self, processor):
        """Test supported image format detection"""
        # Supported formats
        assert processor.is_supported_image("photo.jpg") is True
        assert processor.is_supported_image("photo.jpeg") is True
        assert processor.is_supported_image("photo.png") is True
        assert processor.is_supported_image("photo.gif") is True
        assert processor.is_supported_image("photo.bmp") is True
        assert processor.is_supported_image("photo.tiff") is True
        assert processor.is_supported_image("photo.tif") is True

        # Case insensitive
        assert processor.is_supported_image("PHOTO.JPG") is True
        assert processor.is_supported_image("Photo.PNG") is True

        # Unsupported formats
        assert processor.is_supported_image("document.pdf") is False
        assert processor.is_supported_image("video.mp4") is False
        assert processor.is_supported_image("file.txt") is False

    def create_test_image(self, mode="RGB", size=(100, 100), has_transparency=False):
        """Helper to create test images"""
        if mode == "RGB":
            img = Image.new("RGB", size, color="red")
        elif mode == "RGBA":
            img = Image.new("RGBA", size, color=(255, 0, 0, 128))
        elif mode == "P":
            img = Image.new("P", size, color=1)
            if has_transparency:
                img.info["transparency"] = 0
        else:
            img = Image.new(mode, size)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    def test_convert_to_webp_rgb(self, processor):
        """Test WebP conversion for RGB images"""
        image_data = self.create_test_image("RGB")

        webp_data = processor.convert_to_webp(image_data, quality=100)

        assert isinstance(webp_data, bytes)
        assert len(webp_data) > 0

        # Verify it's actually WebP
        with Image.open(io.BytesIO(webp_data)) as img:
            assert img.format == "WEBP"

    def test_convert_to_webp_rgba(self, processor):
        """Test WebP conversion for RGBA images (with transparency)"""
        image_data = self.create_test_image("RGBA")

        webp_data = processor.convert_to_webp(image_data, quality=100)

        assert isinstance(webp_data, bytes)
        assert len(webp_data) > 0

        # Verify it's WebP and maintains transparency
        with Image.open(io.BytesIO(webp_data)) as img:
            assert img.format == "WEBP"
            assert img.mode in ("RGBA", "LA")

    def test_convert_to_webp_palette_with_transparency(self, processor):
        """Test WebP conversion for palette images with transparency"""
        image_data = self.create_test_image("P", has_transparency=True)

        webp_data = processor.convert_to_webp(image_data, quality=100)

        assert isinstance(webp_data, bytes)
        assert len(webp_data) > 0

        with Image.open(io.BytesIO(webp_data)) as img:
            assert img.format == "WEBP"

    def test_convert_to_webp_palette_without_transparency(self, processor):
        """Test WebP conversion for palette images without transparency"""
        image_data = self.create_test_image("P", has_transparency=False)

        webp_data = processor.convert_to_webp(image_data, quality=100)

        assert isinstance(webp_data, bytes)
        assert len(webp_data) > 0

        with Image.open(io.BytesIO(webp_data)) as img:
            assert img.format == "WEBP"

    def test_convert_to_webp_invalid_data(self, processor):
        """Test error handling for invalid image data"""
        invalid_data = b"not_an_image"

        with pytest.raises(ImageProcessingError, match="Failed to convert image"):
            processor.convert_to_webp(invalid_data)

    def test_get_image_info(self, processor):
        """Test getting image information"""
        image_data = self.create_test_image("RGB", size=(200, 150))

        info = processor.get_image_info(image_data)

        assert info["format"] == "PNG"
        assert info["mode"] == "RGB"
        assert info["size"] == (200, 150)
        assert info["has_transparency"] is False

    def test_get_image_info_with_transparency(self, processor):
        """Test getting image info for images with transparency"""
        image_data = self.create_test_image("RGBA")

        info = processor.get_image_info(image_data)

        assert info["mode"] == "RGBA"
        assert info["has_transparency"] is True

    def test_get_image_info_palette_with_transparency(self, processor):
        """Test getting image info for palette images with transparency"""
        image_data = self.create_test_image("P", has_transparency=True)

        info = processor.get_image_info(image_data)

        assert info["mode"] == "P"
        assert info["has_transparency"] is True

    def test_get_image_info_invalid_data(self, processor):
        """Test error handling for invalid image data in get_image_info"""
        invalid_data = b"not_an_image"

        with pytest.raises(ImageProcessingError, match="Failed to get image info"):
            processor.get_image_info(invalid_data)
