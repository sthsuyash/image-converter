class S3ImageConverterError(Exception):
    """
    Base exception for S3 Image Converter
    """

    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "An error occurred in S3 Image Converter."
        super().__init__(message, *args)
        self.details = kwargs


class S3ConnectionError(S3ImageConverterError):
    """
    Raised when S3 connection fails
    """

    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "Failed to connect to S3."
        super().__init__(message, *args, **kwargs)


class ImageProcessingError(S3ImageConverterError):
    """
    Raised when image processing fails
    """

    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "Image processing failed."
        super().__init__(message, *args, **kwargs)


class ConfigurationError(S3ImageConverterError):
    """
    Raised when configuration is invalid
    """

    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "Invalid configuration."
        super().__init__(message, *args, **kwargs)


class ConversionError(S3ImageConverterError):
    """
    Raised when image conversion fails
    """

    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "Image conversion failed."
        super().__init__(message, *args, **kwargs)
