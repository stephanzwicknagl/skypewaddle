import os

import json
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal

if not os.path.exists("images"):
    os.mkdir("images")




def get_calls(path):
    """ takes json file path as argument 
    open the json file and load into data
    messages = data['conversations'][0]['MessageList']  (this part should be manually selectable)
    
    for every object in messages
        call get_times to fill the dataframe
    
    df = df.append(get_times return)
    if index already exists, then combine lines
    returns dataframe"""


def get_times(object):
    """ takes an object from json-messages-file 
    returns array call
    check if object is a call
        if not: return
    get call ID
        call[0] = call ID
    is call starting?
        call[1] = datetime
    is call ending?
        call[2] = datetime
        call[3] = duration
        call[4] = weekday of ending
    return call
    """

def extract_values(obj, key):
    """
    copy function from skypewaddle.py
    returns value of 
    """



def main():
    """ calls get_calls to
        get dataframe with all calls
        df: Call ID (index)
            Start Time
            End Time
            Duration
            Weekday 
    """
    df = pd.DataFrame(columns= [
                'Call ID', 
                'Start Time',
                'End Time',
                'Duration',
                'Weekday'], index='Call ID')
    """ save df as csv df.to_csv() """

    """ generates images"""
