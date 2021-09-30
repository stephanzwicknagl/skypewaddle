import os

import json
import datetime
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal
import re
# for my_timezone from location
import pytz

if not os.path.exists("images"):
    os.mkdir("images")




def get_calls(path, my_timezone):
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
        'ID',
        'Start Time',
        'End Time',
        'Duration'
        'Weekday',
        'Caller',
        'Terminator'])
    df.set_index('Call ID', inplace=True)

    f = open(path, 'r', encoding='utf-8')
    data = json.load(f)
    f.close()
    messages = data['conversations'][0]['MessageList']

    for obj in messages:
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
            



def get_times(obj, my_timezone): 
    """ takes a part of the json file and analyzes it
    
    takes an object from json-messages-file 
    returns df call
    get call ID
        call[0] = call ID
        call
    is call starting?
        call[1] = datetime
        who called?
    is call ending?
        call[2] = datetime
        who hung up?
    return call
    """

    content = (extract_values(obj, 'content'))[0]
    # get datetime of event
    time = get_call_time(obj, my_timezone)
    # get caller/terminator of call
    val_from = extract_values(obj, 'from')[0]
    # unique identifier for each call to match start and end later
    call_id = re.findall('callId=\\"(\S+)\\"', content)[0]
    # secondary id identifier for calls before mid 2019(?)
    id_sec = extract_values(obj, 'id')[0]

    start_end = re.findall('type=\\"(\S+)\\"', content)[0]
    if start_end == 'started':
        calls = pd.DataFrame(data={'Call ID': call_id, 'ID': id_sec, 'Start Time': time, 'End Time': np.nan, 'Caller': val_from}, index=['Call ID'])
    elif start_end == 'ended':
        duration = re.findall('<duration>([0-9.]+)</duration>', content)
        if len(duration) != 0:
            duration=float(duration[0])
        else:
            duration=0
        calls = pd.DataFrame(data={'Call ID': call_id, 'ID': id_sec, 'Start Time': np.nan, 'End Time': time, 'Duration': duration, 'Terminator': val_from}, index=['Call ID'])
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

def get_call_time(obj, my_timezone):
    time    =     (extract_values(obj, 'originalarrivaltime'))[0]
    year    =     int(time[0:4])
    month   =     int(time[5:7])
    day     =     int(time[8:10])
    hour    =     int(time[11:13])
    minute  =     int(time[14:16])
    second  =     int(time[17:19])

    return datetime.datetime(year, month, day, hour, minute, second, tzinfo=datetime.timezone.utc).astimezone(pytz.timezone(my_timezone))

def calculate_durations(df):
    """ calculates call duration from skype times

    takes filled dataframe df 
    returns dataframe df filled with duration
    """
    
    for index, row in df.iterrows():
        duration = row['End Time'] - row['Start Time']
        df.loc[index, 'Duration'] = float(duration.seconds)
    return df

def fix_old_ids(df): 
    """This function carries the information
    from the end directive to the correct call id
    
    some end call directives do not referernce the call id, but the 
    message id of the start directive. 
    End Time, Duration, Terminator is carried over to the correct call 
    ID and wrong index is dropped
    """
    
    for index, row in df.iterrows():
        if len(index) <= 13:
            df.loc[df['ID'] == index, 'End Time'] = df.loc[index,'End Time']
            df.loc[df['ID'] == index, 'Duration'] = df.loc[index, 'Duration']
            df.loc[df['ID'] == index, 'Terminator'] = df.loc[index, 'Terminator']
            df.drop(index, inplace=True)

    return df

def assign_date_for_midnight(df, my_timezone):
    for index, row in df.iterrows():
        if row['Start Time'].date() != row['End Time'].date():
            call_id_new = index + '_2'
            date_new = row['End Time'].date()
            start_time_new = datetime.datetime(year=date_new.year, month=date_new.month, 
                                            day=date_new.day, hour=0,minute=0,second=0,
                                            tzinfo=pytz.timezone(my_timezone))
            end_time_new = row['End Time']
            duration_new = float((end_time_new - start_time_new).seconds)
            terminator_new = row['Terminator']

            call_id_pre = index + '_1'
            start_time_pre = row['Start Time']
            date_pre = row['Start Time'].date()
            end_time_pre = datetime.datetime(year=date_pre.year, month=date_pre.month,
                                             day=date_pre.day, hour=23, minute=59, second=59, 
                                             tzinfo=pytz.timezone(my_timezone))
            duration_pre = row['Duration'] - duration_new
            caller_pre = row['Caller']

            call = pd.DataFrame(data={
                                'Call ID': [call_id_pre, call_id_new],
                                'Start Time': [start_time_pre, start_time_new],
                                'End Time': [end_time_pre, end_time_new],
                                'Caller': [caller_pre, np.nan],
                                'Terminator': [np.nan, terminator_new],
                                'Duration': [duration_pre, duration_new],
                                },
                                index=[call_id_pre, call_id_new]
                                )
            call.set_index('Call ID', inplace=True)

            df.drop(df.loc[df.index ==index].index, inplace=True)
            df = df.append(call, ignore_index=True)

    return df

def main():
    """ calls get_calls to
        get dataframe with all calls
        df: Call ID (index)
            Start Time
            End Time
            Duration
            Weekday 
    """
    df = get_calls(path="data/04-07-2021.json", my_timezone="Europe/Berlin")
    print(df)
    """ save df as csv df.to_csv() """
    df.to_csv("data/dataframe.csv")
    """ generates images"""


if __name__ == "__main__":
    main()
