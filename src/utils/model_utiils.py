"""The module for handling the machine learning model operations"""

import os

from config.config import MODEL_CHECKPOINT, WRITEABLE_DIR

# Set the huggingface cache directory to /tmp/, this points to writeable temp memory in lambda
# This needs to be set before importing the transformers library
os.environ["HF_HOME"] = WRITEABLE_DIR
import torch

# AutoModel is the class for loading a trained model from saved parameters, and running tokenised
# data through that model
# AutoTokenizer is the class for loading a trained tokenizer, and tokenizing/detokenizing data
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class ModelHandler:
    """Class for handling the machine learning model"""

    def __init__(self):
        """Load the tokenizer and model from the downloaded model files"""
        # Load the model and tokenizer from /tmp/
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_CHECKPOINT, cache_dir=WRITEABLE_DIR, local_files_only=True
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_CHECKPOINT, cache_dir=WRITEABLE_DIR, local_files_only=True
        )

    def generate_processed_sents(self, normalised_sents):
        """Tokenize, process and decode the results for a list of sents.

        Args:
            normalised_sents (str[]): List of normalised sent strings

        Returns:
            new_processed_sents (str[]): List of processed sent strings
        """
        # I've tested this locally, it seems that this method of batch tokenizing, then processing
        #  sents with the model is faster than with a list comprehension, or for loop on
        #  individual sents. However, this may prove more memory expensive

        # Tokenize a list of sents, creating a list of tokenized sents
        inputs = self.tokenizer(
            normalised_sents,
            truncation=True,
            padding="max_length",
            max_length=128,
            return_tensors="pt",
        )
        # Run the list of tokenized sents through the model
        summaries = self.model.generate(**inputs, max_new_tokens=16)
        # Detokenize the resulting processed sents
        new_processed_sents = [
            self.tokenizer.decode(
                result, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            for result in summaries
        ]
        return new_processed_sents
