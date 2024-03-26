"""The main module for the NLP lambda function"""

import json
import logging
import os

from dotenv import load_dotenv

from config.config import DEFAULT_BATCH_SIZE, ENV_DB_VAR_NAME, SENT_LIST_KEY
from utils.db_utils import DbHandler, check_sent_collection
from utils.model_utils import ModelHandler
from utils.s3_utils import download_new_model
from utils.text_utils import normalise_sent

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Attempt to load env variables from .env if not already set by the SAM config
# NOTE: .env file is not included in git for security reasons
if os.environ.get(ENV_DB_VAR_NAME) is None:
    load_dotenv()

# The global variables outside of the lambda_handler function can be shared between invocations
# if they are on the same machine. This means we must consider race conditions for shared resources.
# Despite this, we gain significant performance increase by sharing the parts that are expensive to
# setup.
db_handler = DbHandler()
logger.info("Connected to db")

# The download_new_model() and initialising the model_handler steps have race conditions where
# two lambdas are spun up at similar times. To handle this I'm implementing a mutex lock with
# mongodb, and a check that model_handler is None. This way, if the lambdas are in separate
# environments, they must still wait, but can both load the models if needed.
db_handler.lock_mutex()
try:
    # If the model_handler has been created by another lambda in the same environment, this will
    # be shared and we don't need to recreate it.
    model_handler
    logger.info("Model already loaded, skipping download")
except NameError:
    logger.info("Model not found, initiating download")
    download_new_model()
    logger.info("Model downloaded")

    model_handler = ModelHandler()
    logger.info("Model and Tokenizer loaded")
db_handler.unlock_mutex()


def lambda_handler(event, context) -> None:
    """Entry point for NLP lambda function

    Args:
        event (json): json object containing the list of sentences (sents) to process
        context (): Unused
    """
    # DEFAULT_BATCH_SIZE is a global parameter, which preserves changes by other invocations.
    # To avoid this make a local variable and change that
    batch_size = DEFAULT_BATCH_SIZE
    # Use a try/except block to allow the lambda to return useful error messages
    try:
        # First attempt to get the sentence list
        full_sent_list = None
        # When directly tested the lambda is passed the sent_list in the top level of the event
        # object
        if SENT_LIST_KEY in event.keys():
            full_sent_list = event[SENT_LIST_KEY]
            if "BATCH_SIZE" in event.keys():
                batch_size = int(event["BATCH_SIZE"])
        # When invoked by the api the lambda is passed the sent_list in the body of the event object
        if "body" in event.keys():
            body = json.loads(event["body"])
            if SENT_LIST_KEY in body.keys():
                full_sent_list = body[SENT_LIST_KEY]
            # Makes testing efficient batch sizes easier
            if "BATCH_SIZE" in body.keys():
                batch_size = int(body["BATCH_SIZE"])
        processed_sents = {}
        # If a sent list has been passed in, continue
        if full_sent_list is not None and len(full_sent_list) > 0:
            # We don't want to waste compute by re-processing the same sents
            full_sent_list = list(set(full_sent_list))
            logger.info("Recieved event %s", full_sent_list[0])
            # Process in batches to reduce memory load when running as lambda. Very important
            # for reducing load when processing a batch of sents with the model
            for i in range(len(full_sent_list) // batch_size + 1):
                sent_batch = full_sent_list[
                    i * batch_size : i * batch_size + batch_size
                ]
                if len(sent_batch) > 0:
                    # Prepare sents for processing by the model by handling non-ascii chars
                    normalised_sent_batch = [
                        normalise_sent(single_sent) for single_sent in sent_batch
                    ]
                    # Check if the normalised sents have already been processed in the database
                    # Use a list of indexes for unprocessed sents so we can keep track of
                    # corresponding original sents and normalised sents
                    old_processed_sents, unprocessed_sent_indexes = (
                        check_sent_collection(
                            db_handler, sent_batch, normalised_sent_batch
                        )
                    )
                    # Get processed sents from unprocessed sents, and record to the database
                    new_processed_sents = process_sents(
                        unprocessed_sent_indexes,
                        sent_batch,
                        normalised_sent_batch,
                    )
                    # Merge processed sentence dictionaries
                    processed_sents = (
                        processed_sents | old_processed_sents | new_processed_sents
                    )
        res = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "isBase64Encoded": False,
            "body": json.dumps(processed_sents),
        }
        return res

    except Exception as e:
        print(str(e))
        return {"statusCode": 500, "body": {"event": event, "exception": str(e)}}


def process_sents(unprocessed_sent_indexes, sent_batch, normalised_sent_batch):
    """Process new sents, add them to the database and return a dictionary of
        original_sent : processed sents

    Args:
        unprocessed_sent_indexes (int[]): Indexes of unprocessed sents in sent_batch and
                                           normalised_sent_batch
        sent_batch (str[]): batch of original sents
        normalised_sent_batch (str[]): batch of normalised sents

    Returns:
        Dict: a dictionary of original_sent : processed sents
    """
    new_processed_sents_dict = {}
    if len(unprocessed_sent_indexes) > 0:
        # We use the indexes in unprocessed_sent_indexes to find the unprocessed sentences in
        # sent_batch and normalised_sent_batch
        new_normalised_sents = [
            normalised_sent_batch[index] for index in unprocessed_sent_indexes
        ]
        new_original_sents = [sent_batch[index] for index in unprocessed_sent_indexes]
        # Tokenize, process and detokenize sents to get processed sents
        new_processed_sents = model_handler.generate_processed_sents(
            new_normalised_sents
        )
        db_handler.store_sents(new_normalised_sents, new_processed_sents)
        new_processed_sents_dict = {
            new_original_sents[index]: processed_sent
            for index, processed_sent in enumerate(new_processed_sents)
        }
    return new_processed_sents_dict
