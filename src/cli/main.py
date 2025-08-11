import click
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.converter import S3ImageConverter
from utils.logger import Logger
from utils.exceptions import S3ImageConverterError
from config.settings import get_settings


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be converted without actually converting",
)
@click.option("--prefix", help="Override S3 prefix from config")
@click.option("--quality", type=int, help="Override WebP quality from config")
@click.option("--max-workers", type=int, help="Override max workers from config")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(dry_run, prefix, quality, max_workers, verbose):
    """Convert images in S3 bucket to WebP format"""

    logger = Logger.get_logger()

    try:
        settings = get_settings()

        if verbose:
            logger.setLevel("DEBUG")

        # Override settings if provided
        if prefix is not None:
            settings.S3_PREFIX = prefix
        if quality is not None:
            settings.WEBP_QUALITY = quality
        if max_workers is not None:
            settings.MAX_WORKERS = max_workers

        logger.info(f"Starting S3 Image Converter")
        logger.info(f"Bucket: {settings.S3_BUCKET_NAME}")
        logger.info(f"Prefix: {settings.S3_PREFIX}")
        logger.info(f"Destination: {settings.S3_DESTINATION_PREFIX}")
        logger.info(f"Quality: {settings.WEBP_QUALITY}")
        logger.info(f"Max Workers: {settings.MAX_WORKERS}")
        logger.info(f"Delete Original: {settings.DELETE_ORIGINAL}")

        converter = S3ImageConverter()

        if dry_run:
            logger.info("DRY RUN MODE - No files will be converted")
            image_keys = converter.get_image_keys()
            logger.info(f"Would convert {len(image_keys)} images:")
            for key in image_keys[:10]:  # Show first 10
                webp_key = converter._generate_webp_key(key)
                logger.info(f"  {key} -> {webp_key}")
            if len(image_keys) > 10:
                logger.info(f"  ... and {len(image_keys) - 10} more")
        else:
            result = converter.convert_images()

            # Print summary
            stats = result["stats"]
            click.echo(f"\n{'='*60}")
            click.echo("CONVERSION SUMMARY")
            click.echo(f"{'='*60}")
            click.echo(f"Total files: {stats['total_files']}")
            click.echo(f"Successful: {stats['successful']}")
            click.echo(f"Failed: {stats['failed']}")
            click.echo(f"Skipped: {stats['skipped']}")
            click.echo(
                f"Duration: {stats['end_time'] - stats['start_time']:.2f} seconds"
            )

            if stats["failed"] > 0:
                click.echo(f"\nFailed conversions:")
                for result in result["results"]:
                    if (
                        not result["success"]
                        and result.get("error") != "Already exists"
                    ):
                        click.echo(f"  ❌ {result['source_key']}: {result['error']}")

            if stats["successful"] > 0:
                # Calculate total compression
                total_original = sum(
                    r.get("original_size", 0) for r in result["results"] if r["success"]
                )
                total_webp = sum(
                    r.get("webp_size", 0) for r in result["results"] if r["success"]
                )
                if total_original > 0:
                    total_compression = (
                        (total_original - total_webp) / total_original
                    ) * 100
                    click.echo(f"\nTotal size reduction: {total_compression:.1f}%")
                    click.echo(f"Original total: {total_original:,} bytes")
                    click.echo(f"WebP total: {total_webp:,} bytes")
                    click.echo(f"Saved: {total_original - total_webp:,} bytes")

    except S3ImageConverterError as e:
        logger.error(f"Conversion error: {str(e)}")
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        click.echo(f"❌ Unexpected error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
