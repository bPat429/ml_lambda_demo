import argparse
import json
import logging

import boto3
from botocore.exceptions import ClientError

from src.config.config import SENT_LIST_KEY

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FUNC_NAME = "arn:aws:lambda:us-east-1:949855064237:function:mlLambdaDemo-NlpDemoLambdaFunction-EW8I14kSj1mB"
DEMO_SENTENCE = "I enjoy sunny days"


def invoke_nlp_lambda(sentence):
    processed_sent = ""
    try:
        lambda_client = boto3.client("lambda")
        logger.info("Invoking lambda...")
        res = lambda_client.invoke(
            FunctionName=FUNC_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps({SENT_LIST_KEY: [sentence]}),
        )
        response_payload = res["Payload"]
        decoded_payload = json.loads(response_payload.read().decode("utf-8"))
        processed_sent = decoded_payload["body"]
        logger.info("Response status code %d", res["StatusCode"])
        logger.info("Response payload %s", processed_sent)
    except ClientError:
        logger.exception("Couldn't invoke function %s.", FUNC_NAME)
        raise
    return processed_sent


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--sentence",
        help="Sentence to be processed by lambda for emotion recognition",
        nargs="?",
    )
    args = parser.parse_args()
    print("Runtime may be up to 5 minutes for cold starts")
    if args.sentence is not None:
        print("Processing: " + args.sentence)
        processed_sent = invoke_nlp_lambda(args.sentence)
    else:
        print("No sentence passed, using demo sentence: " + DEMO_SENTENCE)
        processed_sent = invoke_nlp_lambda(DEMO_SENTENCE)
    print(processed_sent)
