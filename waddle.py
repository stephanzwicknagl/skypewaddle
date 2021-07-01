import os

import json
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal
import re

if not os.path.exists("images"):
    os.mkdir("images")




def get_calls(path):
    """ takes json file path as argument 
    open the json file and load into data
    messages = data['conversations'][0]['MessageList']  (this part should be manually selectable)
    
    for every object in messages
        check if object is a call
        call get_times to fill the dataframe
    
    df = df.append(get_times return)
    if index already exists, then combine lines
    returns dataframe"""
    df = pd.DataFrame(columns=[
        'Call ID',
        'Start Time',
        'End Time',
        'Duration',
        'Weekday'])
    df.set_index('Call ID', inplace=True)

    f = open(path, 'r', encoding='utf-8')
    data = json.load(f)
    f.close()
    messages = data['conversations'][0]['MessageList']

    for obj in messages:
        # not-calls are ignored
        if not is_call(obj):
            continue
        calls = get_times(obj)
        # if call is missed/etc. calls is empty and it is ignored
        if calls is None:
            continue 
        df = df.combine_first(calls)
    
    return df
            



def get_times(obj):
    """ takes an object from json-messages-file 
    returns df call
    get call ID
        call[0] = call ID
    is call starting?
        call[1] = datetime
    is call ending?
        call[2] = datetime
    return call
    """
    content = (extract_values(obj, 'content'))[0]
    time = get_call_time(obj)

    id = re.findall('callId=\\"(\S+)\\"', content)[0]

    start_end = re.findall('type=\\"(\S+)\\"', content)[0]
    if start_end == 'started':
        calls = pd.DataFrame(data={'Call ID': id,'Start Time': time, 'End Time': np.nan}, index=[id])
    elif start_end == 'ended':
        calls = pd.DataFrame(data={'Call ID': id,'Start Time': np.nan, 'End Time': time}, index=[id])
    else:
        return
    calls.set_index('Call ID', inplace=True)
    return calls
    

def is_call(obj):
    if(extract_values(obj, "messagetype") == ['Event/Call']):
        return True
    return False


def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results

def get_call_time(obj):
    time    =     (extract_values(obj, 'originalarrivaltime'))[0]
    year    =     int(time[0:4])
    month   =     int(time[5:7])
    day     =     int(time[8:10])
    hour    =     int(time[11:13])
    minute  =     int(time[14:16])
    second  =     int(time[17:19])

    return datetime.datetime(year, month, day, hour, minute, second)

def main():
    """ calls get_calls to
        get dataframe with all calls
        df: Call ID (index)
            Start Time
            End Time
            Duration
            Weekday 
    """
    df = get_calls(path="data/31-03.json")
    print(df)
    """ save df as csv df.to_csv() """
    df.to_csv("data/dataframe.csv")
    """ generates images"""


if __name__ == "__main__":
    main()
