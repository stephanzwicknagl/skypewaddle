import json
from utils.console import print_step, print_substep
from pick import pick
import re

def extract_conversations(path):
    """
    Extracts all conversations from a file
    """
    print_step("Gathering conversation partners")
    f = open(path, 'r', encoding='utf-8')
    data = json.load(f)
    f.close()
    messages = data['conversations']

    
    options = []
    idxs = {}
    for i in range(0,len(messages)):
        partner = messages[i]['id']
        if re.search('.skype', partner) is None:
            options.append(partner)
            idxs[partner] = i

    title = 'Choose the conversation partner: '
    option, _ = pick(options, title)
    index = idxs[option]
    print_substep("You chose {}".format(option))
    return option,index