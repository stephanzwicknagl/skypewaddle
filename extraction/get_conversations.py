import json
from utils.console import print_step, print_substep
from pick import pick
import re


def extract_conversations(path, test=False):
    """
    Extracts all conversation partners from file and lets user choose one.

    Arguments:
        path {str} -- path to json file from skype structure ['conversations']
        teset {bool} -- if True, then function returns before user input

    Returns:
        option -- the conversation partner picked or if test list of all conversation partners
        indexes -- index of the chosen partner or if test a dictionary with all conversation partner as key and their index as value
    """
    print_step("Gathering conversation partners 👥")
    f = open(path, 'r', encoding='utf-8')
    data = json.load(f)
    f.close()
    messages = data['conversations']

    options = []
    idxs = {}
    for i in range(0, len(messages)):
        partner = messages[i]['id']
        if re.search('.skype', partner) is None:
            options.append(partner)
            idxs[partner] = i

    # if test, return before asking for user input
    if test:
        return options, idxs

    # get user input
    option, _ = pick(options, 'Choose the conversation partner: ')
    index = idxs[option]
    print_substep("You chose [red]{}".format(option))
    return option, index
