import pytest
import os
import tempfile
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing"""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "AWS_DEFAULT_REGION": "us-east-1",
            "S3_BUCKET_NAME": "test-bucket",
            "S3_PREFIX": "images/",
            "S3_DESTINATION_PREFIX": "webp-images",
            "WEBP_QUALITY": "100",
            "DELETE_ORIGINAL": "false",
            "MAX_WORKERS": "2",
            "BATCH_SIZE": "10",
            "LOG_LEVEL": "INFO",
            "LOG_FILE": "test.log",
            "LOG_MAX_BYTES": "10410076",
            "LOG_BACKUP_COUNT": "3",
        },
    ):
        yield


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for tests
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
