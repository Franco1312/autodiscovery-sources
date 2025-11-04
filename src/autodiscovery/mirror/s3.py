"""S3 mirror implementation (optional)."""

import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from autodiscovery.config import Config

logger = logging.getLogger(__name__)


class S3Mirror:
    """S3 mirror manager (optional, no-op if credentials missing)."""

    def __init__(self):
        self.enabled = Config.is_s3_enabled()
        self.bucket = Config.MIRRORS_S3_BUCKET
        self.region = Config.AWS_REGION

        if not self.enabled:
            logger.info("S3 mirroring disabled (missing credentials)")
            self.client = None
        else:
            try:
                self.client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                )
                logger.info(f"S3 mirroring enabled for bucket: {self.bucket}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
                self.client = None
                self.enabled = False

    def mirror_file(
        self,
        local_path: Path,
        key: str,
        version: str,
        filename: str,
    ) -> str | None:
        """
        Upload file to S3.

        Returns S3 key if successful, None otherwise.
        """
        if not self.enabled or not self.client:
            return None

        s3_key = f"{key}/{version}/{filename}"

        try:
            self.client.upload_file(str(local_path), self.bucket, s3_key)
            logger.info(f"Uploaded to S3: s3://{self.bucket}/{s3_key}")
            return s3_key
        except (ClientError, NoCredentialsError) as e:
            logger.warning(f"Failed to upload to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            return None
