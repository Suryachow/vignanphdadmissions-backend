import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    def upload_file(self, file_obj, object_name):
        """Upload a file to an S3 bucket and return the public URL"""
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                # ExtraArgs={'ACL': 'public-read'} # Uncomment if bucket allows public read
            )
            
            # Generate the URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{object_name}"
            return url
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            return None

s3_service = S3Service()
