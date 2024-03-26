"""The module for downloading the model from s3"""

import io
import logging
import os
import shutil
from zipfile import ZipFile

import boto3

from config.config import (
    MODEL_CHECKPOINT,
    MODEL_ZIP_LOCATION,
    SENT_MODEL_FILE,
    WRITEABLE_DIR,
)

logger = logging.getLogger()

BUCKET_NAME = os.environ.get("BUCKET_NAME")

s3 = boto3.resource("s3")


# Huggingface requires the model is stored in a writeable directory, so we copy the model
# to lambda's writeable temp memory at '/tmp/'
# Connect to s3 bucket and download NLP model
def download_new_model():
    """Downloads model from s3 bucket and copies to writeable memory location, which allows it to be
    read later
    """
    # A model may be left over from the last initialization, but we can't guarantee its integrity so
    # delete and download fresh
    if os.path.isdir(MODEL_CHECKPOINT):
        shutil.rmtree(MODEL_CHECKPOINT)
    logger.info("Downloading model")
    s3.meta.client.download_file(BUCKET_NAME, SENT_MODEL_FILE, MODEL_ZIP_LOCATION)
    logger.info("Model downloaded")
    with ZipFile(MODEL_ZIP_LOCATION, "r") as model_zip:
        model_zip.extractall(WRITEABLE_DIR)
    logger.info("Model unzipped to %s", WRITEABLE_DIR)
