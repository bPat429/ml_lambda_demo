"""The module containing important and shared constant values"""

DEFAULT_BATCH_SIZE = 30

# Names of environment variables set by a .env file, or the SAM config
ENV_URI_VAR_NAME = "MONGODB_URI"
ENV_USER_VAR_NAME = "MONGODB_USER"
ENV_PASS_VAR_NAME = "MONGODB_PASS"
ENV_DB_VAR_NAME = "MONGODB_DB_NAME"
ENV_HOST_VAR_NAME = "MONGODB_HOST"
ENV_BUCKET_VAR_NAME = "BUCKET_NAME"

# Key for sents to process, expected in the event object
SENT_LIST_KEY = "sent_list"

# Location of writeable memory
WRITEABLE_DIR = "/tmp/"
# filename of model on s3 bucket
SENT_MODEL_NAME = "t5-base-finetuned-emotion"
SENT_MODEL_FILE = SENT_MODEL_NAME + ".zip"
MODEL_ZIP_LOCATION = WRITEABLE_DIR + SENT_MODEL_FILE
MODEL_CHECKPOINT = WRITEABLE_DIR + SENT_MODEL_NAME

# Mongodb collection name
MONGO_COLLECTION = "nlp_processed_sents"
# Mongodb column names
SENTS_DB_NORM_KEY = "normalised_sent"
SENTS_DB_PROC_KEY = "processed_sent"
# Mongodb mutex lock collection name
MONGO_LOCK_COLLECTION = "lock_collection"
MONGO_LOCK_ID = 1
