import pickle
from abc import ABC, abstractmethod
import logging
from typing import Union
import os

import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class Uploader(ABC):

    @abstractmethod
    def _load_credentials(self):
        """
        Load the credentials into appropriate instance variables
        """
        pass

    @abstractmethod
    def _load_session(self):
        """
        Create the session/service object the uploader will use as an instance variable
        """
        pass

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
        self.AWS_ACCESS_KEY = None
        self.AWS_SECRET_ACCESS_KEY = None
        self._load_credentials()
        self.session = None
        self._load_session()

    def _load_credentials(self):
        self.AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    def _load_session(self):
        self.session = boto3.Session(aws_access_key_id=self.AWS_ACCESS_KEY,
                                     aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY)

    def upload_file(self, file_name: str, object_name: str = None) -> bool:
        """Upload a file to an S3 bucket """

        s3 = self.session.client('s3')

        if object_name is None:
            object_name = file_name

        bucket = os.getenv("BUCKET_NAME")

        try:
            response = s3.upload_file(file_name, bucket, object_name)
            logger.info(f"{file_name} uploaded as {object_name} successfully.")
        except ClientError as e:
            logger.error(f"{file_name} failed to upload: {e}")
            return False
        return True


class GDriveUploader(Uploader):

    def __init__(self):
        self.creds = None
        self._load_credentials()
        self.session = None
        self._load_session()

    def _load_credentials(self):
        TOKEN = '.gdrivetoken.pickle'
        if os.path.exists(TOKEN):
            with open(TOKEN, 'rb') as token:
                self.creds = pickle.load(token)
        if not self.creds.valid:
            if self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())

    def _load_session(self):
        self.session = build('drive', 'v3', credentials=self.creds,
                             cache_discovery=False)  # oauth >= 4.0 bug, needs cache_discovery=False, or alternatively:
        # https://github.com/googleapis/google-api-python-client/issues/325#issuecomment-274349841

    def upload_file(self, file_name: str, object_name: str = None) -> bool:
        if object_name is None:
            object_name = file_name
        file_metadata = {
            'name': object_name,
            'mimeType': '*/*'
        }
        media = MediaFileUpload(file_name,
                                mimetype='*/*',
                                resumable=True)
        file = self.session.files().create(body=file_metadata, media_body=media, fields='id').execute()
        if file.get('id'):
            return True
        else:
            return False


def build_uploader(service: str) -> Union[Uploader, None]:
    """
    Factory function to build the uploader object based on which service is specified.
    Currently supports: 's3'

    :param service: string representing service selection
    :return: an uploader object
    """
    if service.lower() == 's3':
        return AWSUploader()
    elif service.lower() == 'gdrive':
        return GDriveUploader()
    return None
