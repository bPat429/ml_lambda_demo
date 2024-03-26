"""The module for handling database operations"""

import logging
import os
import time

from pymongo import ASCENDING, MongoClient

from config.config import (
    ENV_DB_VAR_NAME,
    ENV_HOST_VAR_NAME,
    ENV_PASS_VAR_NAME,
    ENV_URI_VAR_NAME,
    ENV_USER_VAR_NAME,
    MONGO_COLLECTION,
    MONGO_LOCK_COLLECTION,
    MONGO_LOCK_ID,
    SENTS_DB_NORM_KEY,
    SENTS_DB_PROC_KEY,
)

logger = logging.getLogger()


def get_mongodb_uri(mongodb_user, mongodb_pass, mongodb_host):
    """
    Utility function to return the MongoDb uri address.

    :return: MongoDb uri
    """
    # Prioritise composing a URI form user/pass/host values, as these are set in the deploy_x
    # scripts, and not the uri
    if (
        mongodb_user is None
        or len(mongodb_user) == 0
        or mongodb_pass is None
        or len(mongodb_pass) == 0
        or mongodb_host is None
        or len(mongodb_host) == 0
    ):
        uri = os.environ.get(ENV_URI_VAR_NAME)
    else:
        uri = (
            f"mongodb+srv://{mongodb_user}:{mongodb_pass}@{mongodb_host}"
            "/?retryWrites=true&w=majority"
        )
    logger.info("MONGO_DB_URI=%s", uri)

    return uri


def check_sent_collection(db_handler, full_sents, normalised_sents):
    """Function for checking if a sent already exists in the mongodb table for processed sents.
    Then return a dictionary of strings with full_sent as the key, and processed_sent as the
    value. Also return a list of indexes for unprocessed sents.

    Args:
        full_sents (str[]): List of full sents
        normalised_sents (str[]): List of normalised sents

    Returns:
        processed_sents (Dict): A dictionary of already processed sents with full_sent as the
                                 key, and processed_sent as the value
        unprocessed_sent_indexes (int[]): A list of indexes for unprocessed sents.
    """
    # check mongodb database for sents
    matching_sents_dict = db_handler.find_many_sents(
        {SENTS_DB_NORM_KEY: normalised_sents}
    )
    if len(matching_sents_dict) > 0:
        # Format results into a list of (sent_index, is_repeat, processed_sent) tuples
        repeat_sent_tuples = [
            (
                index,
                sent in matching_sents_dict,
                matching_sents_dict[sent] if sent in matching_sents_dict else None,
            )
            for index, sent in enumerate(normalised_sents)
        ]

        # Filter the sents we already have results for into processed_sents dict
        processed_sents = {
            full_sents[index]: processed_sent
            for index, is_repeat, processed_sent in repeat_sent_tuples
            if is_repeat
        }
        # Filter indexes of sents which we don't yet have results for into
        # unprocessed_sent_indexes list
        unprocessed_sent_indexes = [
            index
            for index, is_repeat, processed_sent in repeat_sent_tuples
            if not is_repeat
        ]
    else:
        processed_sents = {}
        unprocessed_sent_indexes = [range(len(normalised_sents))]
    return processed_sents, unprocessed_sent_indexes


class DbHandler:
    """Class for handling all database methods"""

    def __init__(self):
        """Initialise the database connection"""
        mongodb_user = os.environ.get(ENV_USER_VAR_NAME)
        mongodb_pass = os.environ.get(ENV_PASS_VAR_NAME)
        mongodb_db_name = os.environ.get(ENV_DB_VAR_NAME)
        mongodb_host = os.environ.get(ENV_HOST_VAR_NAME)
        mongodb_uri = get_mongodb_uri(mongodb_user, mongodb_pass, mongodb_host)
        self.mongo_client = MongoClient(host=mongodb_uri)
        self.mongo_db = self.mongo_client[mongodb_db_name]
        self.mongo_col = self.mongo_db[MONGO_COLLECTION]
        self.lock_col = self.mongo_db[MONGO_LOCK_COLLECTION]
        # Ensure there is an index on the 'normalised_sent' key, which is the main searched field
        # This increases efficiency when finding later
        self.mongo_col.create_index(
            [(SENTS_DB_NORM_KEY, ASCENDING)], name="search_index", unique=True
        )

    def lock_mutex(self):
        """Mutex lock implementation using mongodb"""
        lock_acquired = False
        while not lock_acquired:
            # Try to lock the mutex
            res = self.lock_col.update_one(
                {"_id": MONGO_LOCK_ID}, {"$set": {"locked": True}}, upsert=True
            )
            # res includes the number of records modified. If the lock was unlocked
            # then the modified count > 0. If it's already locked, the modified count == 0s
            # If the record didn't exist, the modified_count is 0, but the upserted_id is not None.
            # Otherwise the upserted_id is None
            lock_acquired = res.modified_count > 0 or res.upserted_id
            # implement a delay to avoid spamming mongodb and eating up cpu time
            # Use 10 seconds because model loading takes a long time, so losing 10 seconds isn't
            # proportionally significant
            time.sleep(10)

    def unlock_mutex(self):
        """Unlock the mutex lock"""
        res = self.lock_col.update_one(
            {"_id": MONGO_LOCK_ID}, {"$set": {"locked": False}}, upsert=True
        )
        if res.modified_count == 0:
            # Raise an exception if it's aready unlocked, because something must have gone wrong
            raise Exception("Trying to unlock mutex, but already unlocked")

    # Use batch operations to improve performance
    def find_many_sents(self, normalised_sents):
        """Check for documents in database with matching normalised sentences, return
          processed sentences for each match

        Args:
            normalised_sents (list): list of sentences to search for

        Returns:
            matched_sents (Dict): Dictionary of matched sentences
              normalised_sent : processed_sent
        """
        matched_sents = {}
        # Use try and except here to allow the lambda to continue functioning if the non-essential
        #  database operations fail
        try:
            if normalised_sents and len(normalised_sents) > 0:
                logger.info(
                    "Sentencess passed, looking for %d documents", len(normalised_sents)
                )
                # Using 'cursor_type=CursorType.EXHAUST' to get all results immediately causes an
                #  error: database error: OP_QUERY is no longer supported.
                matched_sents_responses = self.mongo_col.find(
                    {SENTS_DB_NORM_KEY: {"$in": normalised_sents}}
                )

                if matched_sents_responses:
                    # Convert list of documents into dict of (normalised_sent : processed_sent)
                    matched_sents = {
                        doc[SENTS_DB_NORM_KEY]: doc[SENTS_DB_PROC_KEY]
                        for doc in matched_sents_responses
                    }
                    logger.info("Matched Sentences found: %d", len(matched_sents))
        except Exception as e:
            logger.info(str(e))
        return matched_sents

    def store_sents(self, normalised_sents, processed_sents):
        """Handles inserting several sentence pairs to the database

        Args:
            normalised_sents (str[]): List of normalised sentences
            processed_sents (str[]): List of processed sentences
        """
        documents = [
            {
                SENTS_DB_NORM_KEY: normalised_sent,
                SENTS_DB_PROC_KEY: processed_sents[index],
            }
            for index, normalised_sent in enumerate(normalised_sents)
        ]
        # Use try and except here to allow the lambda to continue functioning if the non-essential
        #  database operations fail
        try:
            if len(documents) > 0:
                response = self.mongo_col.insert_many(documents)
                if response:
                    print(response)
                    logger.info("Many Sentences inserted")
        except Exception as e:
            logger.info(str(e))
