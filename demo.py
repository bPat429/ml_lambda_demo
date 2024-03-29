import argparse
import json
import logging

import boto3
from botocore.exceptions import ClientError

from src.config.config import SENT_LIST_KEY

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEMO_SENTENCE = "I enjoy sunny days"


def invoke_nlp_lambda(sentence, func_arn):
    """Function for invoking an AWS lambda function synchronously and directly

    Args:
        sentence (string): String to process in the lambda
        func_arn (string): ARN of lambda to run

    Returns:
        processed_sent (string): Processed sentence
    """
    try:
        lambda_client = boto3.client("lambda")
        logger.info("Invoking lambda...")
        res = lambda_client.invoke(
            FunctionName=func_arn,
            InvocationType="RequestResponse",
            Payload=json.dumps({SENT_LIST_KEY: [sentence]}),
        )
        response_payload = res["Payload"]
        decoded_payload = json.loads(response_payload.read().decode("utf-8"))
        processed_sent = decoded_payload["body"]
        logger.info("Response status code %d", res["StatusCode"])
        logger.info("Response payload %s", processed_sent)
    except ClientError:
        logger.exception("Couldn't invoke function %s.", func_arn)
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
    parser.add_argument(
        "-arn", "--lambda_arn", help="Lambda arn to invoke", required=True
    )
    args = parser.parse_args()
    print("Runtime may be up to 5 minutes for cold starts")
    if args.sentence is not None:
        print("Processing: " + args.sentence)
        processed_val = invoke_nlp_lambda(args.sentence, args.lambda_arn)
    else:
        print("No sentence passed, using demo sentence: " + DEMO_SENTENCE)
        processed_val = invoke_nlp_lambda(DEMO_SENTENCE, args.lambda_arn)
    print(processed_val)
