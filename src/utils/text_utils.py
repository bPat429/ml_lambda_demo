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
    normalised_sent = sent.lower()
    # Convert emojis to plain text
    normalise_sent = demoji.replace_with_desc(normalise_sent, sep="")
    # Convert non ascii characters to ascii equivalent
    normalise_sent = unidecode(normalise_sent)
    return normalise_sent.strip()
