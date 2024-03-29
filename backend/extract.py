import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import lxml.etree as ET


def extract_conversations(conversations):
    """
    Extracts all conversation partners from file and lets user choose one.

    Arguments:
        path {str} -- path to json file from skype structure ['conversations']
        teset {bool} -- if True, then function returns before user input

    Returns:
        option -- the conversation partner picked or if test list of all conversation partners
        indexes -- index of the chosen partner or if test a dictionary with all conversation partner as key and their index as value
    """

    participants = []
    for i in range(0, len(conversations)):
        userid = conversations[i]['id']
        if not userid.endswith('.skype'):
            partner = conversations[i]['displayName'] if conversations[i]['displayName'] \
                is not None and userid.startswith('8:') else userid
            participants.append({'label': partner, 'username': userid})
    return participants


def get_calls(set_progress, conversations, partner_index, my_timezone):
    """ takes json file path and extracts call data

    Arguments:
        path {str} -- path to json file from skype structure ['conversations'][partner_index]['MessageList']
        partner_index {str} -- index of the conversation partner
        my_timezone {str} -- timezone of interest

    Returns:
        pd.DataFrame -- dataframe with call data
    """

    # initialize dataframe
    df = pd.DataFrame(columns=[
        'Call ID', 'ID', 'Start Time', 'End Time', 'Duration', 'Weekday',
        'Caller', 'Terminator'
    ])
    df.set_index('Call ID', inplace=True)

    messages = conversations[partner_index]['MessageList']

    # iterate over messages with a progress bar
    for i,obj in enumerate(messages):
        set_progress((str(i), str(len(messages))))
        # not-calls are ignored
        if not is_call(obj):
            continue

        # extract call data
        try:
            calls = get_times(obj, my_timezone)
        except KeyError:
            raise ValueError("The json file is malformed.")
        # missed calls are ignored
        # if call is missed/etc. calls is empty
        if calls is None:
            continue

        # update dataframe with the call
        # if call id already exists, then combine lines
        df = df.combine_first(calls)

    if df.isna().sum().sum() > 0.1 * len(df) * len(df.columns):
        raise ValueError(
            "There are too many missing values in the call dataframe.")

    # some old calls don't reference call id carry information over
    df = fix_old_ids(df)

    # calls that span over two days are split at midnight
    df = assign_date_for_midnight(df, my_timezone)

    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["End Time"] = pd.to_datetime(df["End Time"])
    start_date = df["Start Time"].min().date()
    end_date = df["Start Time"].max().date()
    if pd.isnull(start_date) or pd.isnull(end_date):
        raise ValueError("No calls found in the selected time range.")

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
            df.loc[df['ID'] == index, 'End Time'] = df.loc[index, 'End Time']
            df.loc[df['ID'] == index, 'Duration'] = df.loc[index, 'Duration']
            df.loc[df['ID'] == index, 'Terminator'] = df.loc[index,
                                                             'Terminator']
            df.drop(index, inplace=True)

    return df


def is_call(obj):
    if obj['messagetype'] == 'Event/Call':
        return True
    return False


def get_times(obj, my_timezone):
    """ takes one object from the json file and analyzes it
    
    Arguments:
        obj {dict} -- one object from the json file
        my_timezone {str} -- timezone of interest
    
    Returns:
        pd.DataFrame -- dataframe with call data
                        [ID, Start Time, End Time, Duration, Weekday, Caller Terminator]
    """
    content = ET.fromstring(obj['content'], parser=ET.XMLParser(encoding='utf-8'))

    # get datetime of event
    time = get_call_time(obj, my_timezone)
    # get caller/terminator of call
    val_from = obj['from']
    # unique identifier for each call to match start and end later
    call_id = content.get('callId')
    # secondary id identifier for calls before mid 2019(?)
    id_sec = obj['id']

    event_category = content.get('type')
    if event_category == 'started':
        calls = pd.DataFrame(data={
            'Call ID': call_id,
            'ID': id_sec,
            'Start Time': time,
            'End Time': np.nan,
            'Caller': val_from,
            'Weekday': time.weekday(),
        },
                                index=['Call ID'])
    elif event_category == 'ended':
        duration = content.xpath('.//part[1]/duration/text()')
        if len(duration) != 0:
            duration = float(duration[0])
        else:
            duration = 0
        calls = pd.DataFrame(data={
            'Call ID': call_id,
            'ID': id_sec,
            'Start Time': np.nan,
            'End Time': time,
            'Duration': duration,
            'Terminator': val_from
        },
                                index=['Call ID'])
    else:
        return
    calls.set_index('Call ID', inplace=True)
    return calls


def get_call_time(obj, my_timezone):
    time = obj['originalarrivaltime']
    year = int(time[0:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    minute = int(time[14:16])
    second = int(time[17:19])

    moment = datetime.datetime(year,
                            month,
                            day,
                            hour,
                            minute,
                            second,
                            tzinfo=ZoneInfo('Etc/UTC')).astimezone(
                                ZoneInfo(my_timezone))
    return moment


def assign_date_for_midnight(df, my_timezone):
    """Split calls that span over two days at midnight
    
    Arguments:
        df {pd.DataFrame} -- dataframe with call data
        my_timezone {str} -- timezone of interest
        
    Returns:
        pd.DataFrame -- dataframe with call data
    """

    for index, row in df.iterrows():
        if row['Start Time'].date() != row['End Time'].date():
            if pd.isnull(row['Start Time']) or pd.isnull(row['End Time']):
                continue
            date_2 = row['End Time'].date()
            starttime_2 = datetime.datetime(
                year=date_2.year,
                month=date_2.month,
                day=date_2.day,
                hour=0,
                minute=0,
                second=0,
                tzinfo=ZoneInfo(my_timezone))
            endtime_2 = row['End Time']
            duration_2 = float((endtime_2 - starttime_2).seconds)
            terminator_2 = row['Terminator']

            starttime_1 = row['Start Time']
            date_1 = row['Start Time'].date()
            endtime_1 = datetime.datetime(
                year=date_1.year,
                month=date_1.month,
                day=date_1.day,
                hour=23,
                minute=59,
                second=59,
                tzinfo=ZoneInfo(my_timezone))
            duration_1 = float((endtime_1 - starttime_1).seconds)
            caller_1 = row['Caller']

            call = pd.DataFrame(data={
                'Call ID': [index, index],
                'Start Time': [starttime_1, starttime_2],
                'End Time': [endtime_1, endtime_2],
                'Caller': [caller_1, np.nan],
                'Terminator': [np.nan, terminator_2],
                'Duration': [duration_1, duration_2],
                'Weekday': [starttime_1.weekday(),
                            starttime_2.weekday()],
            },
                                index=[index, index])
            call.set_index('Call ID', inplace=True)

            df = df.drop(index)
            df = pd.concat([df, call])

    return df