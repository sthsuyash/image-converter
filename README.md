# S3 Image Converter

A production-grade tool for converting images in S3 buckets to WebP format with parallel processing, comprehensive logging and robust error handling.

## Features

- **Batch Processing**: Convert multiple images simultaneously with configurable concurrency
- **Format Support**: Supports JPG, JPEG, PNG, GIF, BMP, TIFF formats
- **WebP Optimization**: Configurable quality settings with automatic transparency handling
- **Parallel Processing**: Multi-threaded conversion for faster processing
- **Comprehensive Logging**: Detailed logs with rotation and multiple output formats
- **Error Handling**: Robust error handling with detailed error reporting
- **Configuration Management**: Environment-based configuration with validation
- **CLI Interface**: Easy-to-use command-line interface
- **Dry Run Mode**: Preview conversions without making changes
- **Progress Tracking**: Real-time progress updates and statistics
- **Compression Stats**: Detailed compression ratio reporting

## Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    cd s3-image-converter
    ```

2. Create virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Install the package:

    ```bash
    pip install -e .
    ```

## Configuration

1. Copy the example environment file:

    ```bash
    cp .env.example .env
    ```

2. Edit `.env` with your configuration:

    ```env
    # AWS Configuration
    AWS_ACCESS_KEY_ID=your_access_key_here
    AWS_SECRET_ACCESS_KEY=your_secret_key_here
    AWS_DEFAULT_REGION=us-east-1

    # S3 Configuration
    S3_BUCKET_NAME=your-bucket-name
    S3_PREFIX=images/
    S3_DESTINATION_PREFIX=webp-images

    # Conversion Settings
    WEBP_QUALITY=100
    DELETE_ORIGINAL=false
    MAX_WORKERS=4
    BATCH_SIZE=100

    # Logging Configuration
    LOG_LEVEL=INFO
    LOG_FILE=logs/s3_converter.log
    LOG_MAX_BYTES=104100760
    LOG_BACKUP_COUNT=5
    ```

## Usage

### Command Line

```bash
# Basic conversion
s3-convert

# Dry run to preview changes
s3-convert --dry-run

# Override settings
s3-convert --prefix "photos/" --quality 90 --max-workers 8

# Verbose logging
s3-convert --verbose
```

### Python API

```python
from core.converter import S3ImageConverter

# Initialize converter
converter = S3ImageConverter()

# Convert all images
result = converter.convert_images()

# Convert specific images
image_keys = ['image1.jpg', 'image2.png']
result = converter.convert_images(image_keys)

# Access results
print(f"Converted {result['stats']['successful']} images")
print(f"Failed: {result['stats']['failed']}")

# Iterate through individual results
for res in result['results']:
    if res['success']:
        print(f"✅ {res['source_key']} -> {res['destination_key']}")
        print(f"   Size: {res['original_size']} -> {res['webp_size']} bytes")
        print(f"   Compression: {res['compression_ratio']:.1f}%")
    else:
        print(f"❌ {res['source_key']}: {res['error']}")
```

### Direct S3 and Image Processing

```python
from core.s3_client import S3Client
from core.image_processor import ImageProcessor

# S3 operations
s3 = S3Client()
objects = s3.list_objects('images/')
image_data = s3.get_object('images/photo.jpg')

# Image processing
processor = ImageProcessor()
webp_data = processor.convert_to_webp(image_data, quality=100)
info = processor.get_image_info(image_data)
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | None |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | None |
| `AWS_DEFAULT_REGION` | AWS region | us-east-1 |
| `S3_BUCKET_NAME` | S3 bucket name | Required |
| `S3_PREFIX` | Source prefix filter | "" |
| `S3_DESTINATION_PREFIX` | Destination prefix | webp-images |
| `WEBP_QUALITY` | WebP quality (0-100) | 100 |
| `DELETE_ORIGINAL` | Delete original after conversion | false |
| `MAX_WORKERS` | Parallel processing threads | 4 |
| `BATCH_SIZE` | Batch processing size | 100 |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_FILE` | Log file path | logs/s3_converter.log |
| `LOG_MAX_BYTES` | Max log file size | 104100760 |
| `LOG_BACKUP_COUNT` | Log backup files | 5 |

### CLI Options

- `--dry-run`: Preview conversions without executing
- `--prefix TEXT`: Override S3 prefix
- `--quality INTEGER`: Override WebP quality
- `--max-workers INTEGER`: Override worker count
- `--verbose`: Enable debug logging

## Error Handling

The tool includes comprehensive error handling:

- **S3ConnectionError**: AWS/S3 connection issues
- **ImageProcessingError**: Image format or processing errors
- **ConversionError**: Conversion pipeline failures
- **ConfigurationError**: Invalid configuration

## Logging

Logs are written to both console and file with rotation:

- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Automatic log rotation based on file size
- Detailed error context and stack traces
- Performance metrics and statistics

## Performance Considerations

- **Parallel Processing**: Adjustable worker threads for optimal performance
- **Memory Management**: Efficient streaming of large images
- **Batch Processing**: Configurable batch sizes for memory optimization
- **Progress Tracking**: Real-time progress updates for long-running operations

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:

- Create an issue in the GitHub repository
- Check the logs for detailed error information
- Ensure AWS credentials and S3 permissions are correct
