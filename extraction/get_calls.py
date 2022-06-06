import json
import numpy as np
import pandas as pd
from extraction.extract_values import extract_values
from extraction.times import get_times, assign_date_for_midnight
from utils.console import print_step
from rich.progress import track


def get_calls(path, partner_index, my_timezone):
    """ takes json file path as argument 
    open the json file and load into data
    messages = data['conversations'][partner_index]['MessageList']

    for every object in messages
        check if object is a call
        call get_times to fill the dataframe
    
    df = df.append(get_times return)
    if index already exists, then combine lines
    returns dataframe"""

    print_step("Getting all the call details ☎️")
    df = pd.DataFrame(columns=[
        'Call ID',
        'ID',
        'Start Time',
        'End Time',
        'Duration',
        'Weekday',
        'Caller',
        'Terminator'])
    df.set_index('Call ID', inplace=True)

    f = open(path, 'r', encoding='utf-8')
    data = json.load(f)
    f.close()
    messages = data['conversations'][partner_index]['MessageList']


    for obj in track(messages, total=len(messages), description="Processing calls"):
        # not-calls are ignored
        if not is_call(obj):
            continue
        calls = get_times(obj, my_timezone)
        # if call is missed/etc. calls is empty and it is ignored
        if calls is None:
            continue 
        df = df.combine_first(calls)

    df = fix_old_ids(df)
    df = assign_date_for_midnight(df, my_timezone)
    return df


def fix_old_ids(df): 
    """This function carries the information
    from the end directive to the correct call id
    
    some end call directives do not referernce the call id, but the 
    message id of the start directive. 
    End Time, Duration, Terminator is carried over to the correct call 
    ID and wrong index is dropped
    """
    print_step("Cleaning up call IDs 🧹")
    for index, row in track(df.iterrows(), total=len(df), description="Cleaning up"):
        if len(index) <= 13:
            df.loc[df['ID'] == index, 'End Time'] = df.loc[index,'End Time']
            df.loc[df['ID'] == index, 'Duration'] = df.loc[index, 'Duration']
            df.loc[df['ID'] == index, 'Terminator'] = df.loc[index, 'Terminator']
            df.drop(index, inplace=True)

    return df

def is_call(obj):
    if(extract_values(obj, "messagetype") == ['Event/Call']):
        return True
    return False

