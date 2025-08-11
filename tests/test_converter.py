import pytest
from unittest.mock import Mock, patch, MagicMock
import io
from PIL import Image

from core.converter import S3ImageConverter
from utils.exceptions import ConversionError


class TestS3ImageConverter:

    @pytest.fixture
    def mock_settings(self):
        with patch("core.converter.get_settings") as mock:
            settings = Mock()
            settings.S3_PREFIX = "images/"
            settings.S3_DESTINATION_PREFIX = "webp-images"
            settings.WEBP_QUALITY = 100
            settings.DELETE_ORIGINAL = False
            settings.MAX_WORKERS = 2
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_s3_client(self):
        with patch("core.converter.S3Client") as mock:
            yield mock.return_value

    @pytest.fixture
    def mock_image_processor(self):
        with patch("core.converter.ImageProcessor") as mock:
            yield mock.return_value

    @pytest.fixture
    def converter(self, mock_settings, mock_s3_client, mock_image_processor):
        with patch("core.converter.Logger"):
            return S3ImageConverter()

    def test_init(self, converter):
        """Test converter initialization"""
        assert converter.stats["total_files"] == 0
        assert converter.stats["processed"] == 0
        assert converter.stats["successful"] == 0
        assert converter.stats["failed"] == 0
        assert converter.stats["skipped"] == 0

    def test_get_image_keys(self, converter, mock_s3_client, mock_image_processor):
        """Test getting image keys from S3"""
        # Mock S3 objects
        mock_s3_client.list_objects.return_value = [
            {"Key": "images/photo1.jpg"},
            {"Key": "images/photo2.png"},
            {"Key": "images/document.pdf"},  # Not an image
            {"Key": "images/photo3.gif"},
        ]

        # Mock image processor
        mock_image_processor.is_supported_image.side_effect = lambda x: x.endswith(
            (".jpg", ".png", ".gif")
        )

        keys = converter.get_image_keys()

        expected_keys = ["images/photo1.jpg", "images/photo2.png", "images/photo3.gif"]
        assert keys == expected_keys
        mock_s3_client.list_objects.assert_called_once_with("images/")

    def test_get_image_keys_error(self, converter, mock_s3_client):
        """Test error handling in get_image_keys"""
        mock_s3_client.list_objects.side_effect = Exception("S3 error")

        with pytest.raises(ConversionError, match="Failed to get image keys"):
            converter.get_image_keys()

    def test_generate_webp_key(self, converter):
        """Test WebP key generation"""
        # With destination prefix
        result = converter._generate_webp_key("images/photo.jpg")
        assert result == "webp-images/photo.webp"

        # Without destination prefix
        converter.settings.S3_DESTINATION_PREFIX = ""
        result = converter._generate_webp_key("images/photo.jpg")
        assert result == "images/photo.webp"

    def test_convert_single_image_success(
        self, converter, mock_s3_client, mock_image_processor
    ):
        """Test successful single image conversion"""
        source_key = "images/photo.jpg"

        # Mock image data
        original_data = b"fake_image_data"
        webp_data = b"fake_webp_data"

        # Mock S3 operations
        mock_s3_client.get_object.side_effect = [
            Exception("WebP doesn't exist"),  # First call to check WebP existence
            original_data,  # Second call to get original image
        ]

        # Mock image processing
        mock_image_processor.convert_to_webp.return_value = webp_data

        result = converter._convert_single_image(source_key)

        assert result["success"] is True
        assert result["source_key"] == source_key
        assert result["destination_key"] == "webp-images/photo.webp"
        assert result["original_size"] == len(original_data)
        assert result["webp_size"] == len(webp_data)
        assert result["compression_ratio"] > 0

        # Verify S3 operations
        mock_s3_client.put_object.assert_called_once_with(
            "webp-images/photo.webp", webp_data, content_type="image/webp"
        )

    def test_convert_single_image_already_exists(self, converter, mock_s3_client):
        """Test skipping when WebP already exists"""
        source_key = "images/photo.jpg"

        # Mock WebP already exists
        mock_s3_client.get_object.return_value = b"existing_webp_data"

        result = converter._convert_single_image(source_key)

        assert result["success"] is True
        assert result["error"] == "Already exists"
        assert converter.stats["skipped"] == 1

    def test_convert_single_image_with_delete_original(
        self, converter, mock_s3_client, mock_image_processor
    ):
        """Test conversion with original file deletion"""
        converter.settings.DELETE_ORIGINAL = True
        source_key = "images/photo.jpg"

        # Mock S3 operations
        mock_s3_client.get_object.side_effect = [
            Exception("WebP doesn't exist"),
            b"fake_image_data",
        ]
        mock_image_processor.convert_to_webp.return_value = b"fake_webp_data"

        result = converter._convert_single_image(source_key)

        assert result["success"] is True
        mock_s3_client.delete_object.assert_called_once_with(source_key)

    def test_convert_single_image_failure(self, converter, mock_s3_client):
        """Test conversion failure handling"""
        source_key = "images/photo.jpg"

        # Mock S3 error
        mock_s3_client.get_object.side_effect = Exception("S3 error")

        result = converter._convert_single_image(source_key)

        assert result["success"] is False
        assert "S3 error" in result["error"]
        assert converter.stats["failed"] == 1

    def test_convert_images_empty_list(self, converter):
        """Test conversion with empty image list"""
        result = converter.convert_images([])

        assert result["results"] == []
        assert result["stats"]["total_files"] == 0

    def test_convert_images_with_list(
        self, converter, mock_s3_client, mock_image_processor
    ):
        """Test conversion with provided image list"""
        image_keys = ["images/photo1.jpg", "images/photo2.png"]

        # Mock successful conversions
        mock_s3_client.get_object.side_effect = [
            Exception("WebP doesn't exist"),
            b"fake_image_data1",
            Exception("WebP doesn't exist"),
            b"fake_image_data2",
        ]
        mock_image_processor.convert_to_webp.return_value = b"fake_webp_data"

        result = converter.convert_images(image_keys)

        assert len(result["results"]) == 2
        assert result["stats"]["total_files"] == 2
        assert result["stats"]["successful"] == 2
        assert result["stats"]["failed"] == 0

    @patch("core.converter.time.time")
    def test_convert_images_timing(self, mock_time, converter):
        """Test timing statistics"""
        mock_time.side_effect = [1000, 1010]  # 10 seconds duration

        result = converter.convert_images([])

        assert result["stats"]["start_time"] == 1000
        assert result["stats"]["end_time"] == 1010
