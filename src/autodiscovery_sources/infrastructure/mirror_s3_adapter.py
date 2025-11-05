"""S3 adapter for mirror operations (stub implementation)."""

import os
from typing import Optional

from ..domain.errors import MirrorError
from ..interfaces.mirror_port import MirrorPort


class MirrorS3Adapter(MirrorPort):
    """S3 adapter for mirroring files (stub if no credentials)."""

    def __init__(self, bucket: Optional[str] = None, region: Optional[str] = None):
        """Initialize S3 adapter.
        
        If credentials are not available, this is a no-op stub.
        """
        self.bucket = bucket or os.getenv("S3_BUCKET")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self._client = None
        
        # Check if credentials are available
        if self.aws_access_key_id and self.aws_secret_access_key and self.bucket:
            try:
                import boto3
                self._client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region,
                )
            except Exception as e:
                # Stub mode: no-op if boto3 fails
                pass

    def write(self, key: str, version: str, filename: str, content: bytes) -> Optional[str]:
        """Write file to S3 mirror.
        
        TODO: Implement S3 upload when credentials are available.
        Currently a stub that returns None if no credentials.
        """
        if not self._client or not self.bucket:
            # Stub mode: return None (filesystem will be used)
            return None
        
        try:
            # Construct S3 key: {source_key}/{version}/{filename}
            s3_key = f"{key}/{version}/{filename}"
            
            # Upload to S3
            self._client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content,
                ContentType="application/octet-stream",
            )
            
            return s3_key
        except Exception as e:
            # Fallback: don't fail, just log and return None
            # This allows filesystem mirror to handle it
            return None

