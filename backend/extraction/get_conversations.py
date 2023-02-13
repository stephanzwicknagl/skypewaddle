import json
from utils.console import print_step, print_substep
from pick import pick
import re
import io
import base64


def extract_conversations(coded_data, test=False):
    """
    Extracts all conversation partners from file and lets user choose one.

    Arguments:
        path {str} -- path to json file from skype structure ['conversations']
        teset {bool} -- if True, then function returns before user input

    Returns:
        option -- the conversation partner picked or if test list of all conversation partners
        indexes -- index of the chosen partner or if test a dictionary with all conversation partner as key and their index as value
    """
    decoded_data = base64.b64decode(coded_data)
    data = json.load(io.BytesIO(decoded_data))
    messages = data['conversations']

    options = []
    idxs = {}
    for i in range(0, len(messages)):
        partner = messages[i]['id']
        if re.search('.skype', partner) is None:
            options.append(partner)
            idxs[partner] = i

    # if test, return before asking for user input
    return options, idxs
