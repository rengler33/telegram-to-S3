from abc import ABC, abstractmethod
import logging
from typing import Union
import os

import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class Uploader(ABC):

    @abstractmethod
    def upload_file(self, file_name: str, object_name: str = None) -> bool:
        """
        Upload a file to a storage location

        :param file_name: name of file that needs to be uploaded
        :param object_name: Optional, name of file to be used in destination (use file_name if not provided)
        :return: True if file was uploaded, else False
        """
        pass


class AWSUploader(Uploader):

    def __init__(self):
        self.service = 'S3'
        self.AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.BUCKET_NAME = os.getenv("BUCKET_NAME")
        self.session = boto3.Session(aws_access_key_id=self.AWS_ACCESS_KEY,
                                     aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY)

    def upload_file(self, file_name: str, object_name: str = None) -> bool:
        """Upload a file to an S3 bucket """

        s3 = self.session.client('s3')

        if object_name is None:
            object_name = file_name

        bucket = self.BUCKET_NAME

        try:
            response = s3.upload_file(file_name, bucket, object_name)
            logger.info(f"{file_name} uploaded as {object_name} successfully.")
        except ClientError as e:
            logger.error(f"{file_name} failed to upload: {e}")
            return False
        return True


def build_uploader(service: str) -> Union[Uploader, None]:
    """
    Factory function to build the uploader object based on which service is specified.
    Currently supports: 's3'

    :param service: string representing service selection
    :return: an uploader object
    """
    if service.lower() == 's3':
        return AWSUploader()
    return None
