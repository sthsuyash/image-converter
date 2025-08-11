import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError

from core.s3_client import S3Client
from utils.exceptions import S3ConnectionError


class TestS3Client:

    @pytest.fixture
    def mock_settings(self):
        with patch("core.s3_client.get_settings") as mock:
            settings = Mock()
            settings.AWS_ACCESS_KEY_ID = "test_key"
            settings.AWS_SECRET_ACCESS_KEY = "test_secret"
            settings.AWS_DEFAULT_REGION = "us-east-1"
            settings.S3_BUCKET_NAME = "test-bucket"
            mock.return_value = settings
            yield settings

    @pytest.fixture
    def mock_boto3_client(self):
        with patch("core.s3_client.boto3.client") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def s3_client(self, mock_settings, mock_boto3_client):
        with patch("core.s3_client.Logger"):
            return S3Client()

    def test_init_success(self, mock_settings, mock_boto3_client):
        """Test successful S3 client initialization"""
        with patch("core.s3_client.Logger"):
            client = S3Client()

            mock_boto3_client.assert_called_once_with(
                "s3",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                region_name="us-east-1",
            )
            mock_boto3_client.return_value.head_bucket.assert_called_once_with(
                Bucket="test-bucket"
            )

    def test_init_no_credentials(self, mock_settings, mock_boto3_client):
        """Test initialization with no credentials"""
        mock_boto3_client.side_effect = NoCredentialsError()

        with patch("core.s3_client.Logger"):
            with pytest.raises(S3ConnectionError, match="AWS credentials not found"):
                S3Client()

    def test_init_bucket_not_found(self, mock_settings, mock_boto3_client):
        """Test initialization with non-existent bucket"""
        error = ClientError(
            error_response={"Error": {"Code": "404"}}, operation_name="HeadBucket"
        )
        mock_boto3_client.return_value.head_bucket.side_effect = error

        with patch("core.s3_client.Logger"):
            with pytest.raises(S3ConnectionError, match="Bucket test-bucket not found"):
                S3Client()

    def test_init_access_denied(self, mock_settings, mock_boto3_client):
        """Test initialization with access denied"""
        error = ClientError(
            error_response={"Error": {"Code": "403"}}, operation_name="HeadBucket"
        )
        mock_boto3_client.return_value.head_bucket.side_effect = error

        with patch("core.s3_client.Logger"):
            with pytest.raises(
                S3ConnectionError, match="Access denied to bucket test-bucket"
            ):
                S3Client()

    def test_list_objects_success(self, s3_client, mock_boto3_client):
        """Test successful object listing"""
        # Mock paginator
        paginator = Mock()
        mock_boto3_client.get_paginator.return_value = paginator

        # Mock pages
        pages = [
            {"Contents": [{"Key": "file1.jpg"}, {"Key": "file2.png"}]},
            {"Contents": [{"Key": "file3.gif"}]},
            {},  # Empty page
        ]
        paginator.paginate.return_value = pages

        objects = s3_client.list_objects("images/")

        expected_objects = [
            {"Key": "file1.jpg"},
            {"Key": "file2.png"},
            {"Key": "file3.gif"},
        ]
        assert objects == expected_objects

        mock_boto3_client.get_paginator.assert_called_once_with("list_objects_v2")
        paginator.paginate.assert_called_once_with(
            Bucket="test-bucket", Prefix="images/"
        )

    def test_list_objects_error(self, s3_client, mock_boto3_client):
        """Test error handling in list_objects"""
        error = ClientError(
            error_response={"Error": {"Code": "500"}}, operation_name="ListObjectsV2"
        )
        mock_boto3_client.get_paginator.side_effect = error

        with pytest.raises(S3ConnectionError, match="Failed to list objects"):
            s3_client.list_objects("images/")

    def test_get_object_success(self, s3_client, mock_boto3_client):
        """Test successful object retrieval"""
        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = b"file_content"
        mock_boto3_client.get_object.return_value = mock_response

        content = s3_client.get_object("test-key")

        assert content == b"file_content"
        mock_boto3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-key"
        )

    def test_get_object_error(self, s3_client, mock_boto3_client):
        """Test error handling in get_object"""
        error = ClientError(
            error_response={"Error": {"Code": "404"}}, operation_name="GetObject"
        )
        mock_boto3_client.get_object.side_effect = error

        with pytest.raises(S3ConnectionError, match="Failed to get object test-key"):
            s3_client.get_object("test-key")

    def test_put_object_success(self, s3_client, mock_boto3_client):
        """Test successful object upload"""
        result = s3_client.put_object("test-key", b"content", "image/webp")

        assert result is True
        mock_boto3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-key",
            Body=b"content",
            ContentType="image/webp",
        )

    def test_put_object_error(self, s3_client, mock_boto3_client):
        """Test error handling in put_object"""
        error = ClientError(
            error_response={"Error": {"Code": "403"}}, operation_name="PutObject"
        )
        mock_boto3_client.put_object.side_effect = error

        with pytest.raises(S3ConnectionError, match="Failed to put object test-key"):
            s3_client.put_object("test-key", b"content")

    def test_delete_object_success(self, s3_client, mock_boto3_client):
        """Test successful object deletion"""
        result = s3_client.delete_object("test-key")

        assert result is True
        mock_boto3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-key"
        )

    def test_delete_object_error(self, s3_client, mock_boto3_client):
        """Test error handling in delete_object"""
        error = ClientError(
            error_response={"Error": {"Code": "500"}}, operation_name="DeleteObject"
        )
        mock_boto3_client.delete_object.side_effect = error

        with pytest.raises(S3ConnectionError, match="Failed to delete object test-key"):
            s3_client.delete_object("test-key")
