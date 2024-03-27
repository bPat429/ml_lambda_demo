"""The module for normalising sentences"""

import demoji
from unidecode import unidecode


def normalise_sent(sent):
    """Function for normalising sentences for use with an ascii only NLP model

    Args:
        sent (string): sentence to normalise
    """
    # Important to normalise the sentence before checking the mongodb table to avoid similar
    # sentences being processed and stored twice with identical results
    # Convert to lowercase
    normalised_val = sent.lower()
    # Convert emojis to plain text
    normalised_val = demoji.replace_with_desc(normalised_val, sep="")
    # Convert non ascii characters to ascii equivalent
    normalised_val = unidecode(normalised_val)
    return normalised_val.strip()
