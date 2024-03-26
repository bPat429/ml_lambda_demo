import argparse
import json
import logging

import boto3
from botocore.exceptions import ClientError

from src.config.config import SENT_LIST_KEY

logger = logging.getLogger()

FUNC_NAME = "nlp_lambda_demo"
demo_sentence = "I enjoy sunny days"


def invoke_nlp_lambda(sentence):
    try:
        lambda_client = boto3.client("lambda")
        res = lambda_client.invoke(
            FunctionName=FUNC_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps({"SENT_LIST_KEY": [sentence]}),
        )
    except ClientError:
        logger.exception("Couldn't invoke function %s.", FUNC_NAME)
        raise
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sentence", help="Sentence to be processed by lambda")
    args = parser.parse_args()
    if args.sentence is not None:
        print("Processing: " + args.sentence)
        invoke_nlp_lambda(args.sentence)
    else:
        print("No sentence passed, processing demo sentence " + demo_sentence)
        invoke_nlp_lambda(demo_sentence)
