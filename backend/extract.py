import re
import ijson

import numpy as np
import pandas as pd

import datetime
import re

import numpy as np
import pandas as pd
import pytz


def extract_conversations(data):
    """
    Extracts all conversation partners from file and lets user choose one.

    Arguments:
        data {io.BytesIO} -- 

    Returns:
        conversations {Dict} -- Conversation partners, filtered from some automated skype data
    """
    conversations = []
    for prefix, _, value in ijson.parse(data):
        if prefix == 'conversations.item.id' and re.search('.skype', value) is None:
            conversations.append(value)
    return conversations

def get_parser_next(set_progress, parser, upload_size):
    """ creates ijson parser

    Arguments:
    :param set_progress: function to set progress bar
    :param parser: enumerator of ijson parser
    :param upload_size: size of uploaded file

    Returns:
        ijson.parser.Parser -- ijson parser
    """
    i, (prefix, event, value) = next(parser)
    # Estimate Progress:
    set_progress((str(i), str(upload_size/40)))
    return prefix, event, value

def get_calls(set_progress, data, partner_index, my_timezone, upload_size):
    """ takes data as filelike buffer and extracts call data 

    Arguments:
    :param set_progress: function to set progress bar
    :param data: filelike buffer
    :param partner_index: index of partner in conversations
    :param my_timezone: timezone of user
    :param upload_size: size of uploaded file

    Returns:
        pd.DataFrame -- dataframe with call data
    """

    # initialize dataframe
    df = pd.DataFrame(columns=[
        'Call ID', 'ID', 'Start Time', 'End Time', 'Duration', 'Weekday',
        'Caller', 'Terminator'
    ])
    df.set_index('Call ID', inplace=True)

    parser = enumerate(ijson.parse(data))

    while True:
        prefix, event, value = get_parser_next(set_progress, parser, upload_size)

        if (prefix, value) == ('conversations.item.id', partner_index['label']):
            id_sec, time, content, message_from = None, None, None, None

            while prefix != 'conversations.item.MessageList.item':
                prefix, event, value = get_parser_next(set_progress, parser, upload_size)

            while prefix.startswith('conversations.item.MessageList.item'):

                # secondary ID
                if prefix == 'conversations.item.MessageList.item.id':
                    id_sec = value

                # Call time
                if prefix == 'conversations.item.MessageList.item.originalarrivaltime':
                    time = get_call_time(value, my_timezone)

                # Type of message (skips when not a call)
                if prefix == 'conversations.item.MessageList.item.messagetype':
                    if value != "Event/Call":
                        # skip to end_map
                        while event != 'end_map':
                            prefix, event, value = get_parser_next(set_progress, parser, upload_size)
                            

                # Call content
                if prefix == 'conversations.item.MessageList.item.content':
                    content = value

                # Call initiator
                if prefix == 'conversations.item.MessageList.item.from':
                    message_from = value

                # End of Message Object
                if event == 'end_map':
                    if (id_sec is not None and
                        time is not None and
                        content is not None and
                        message_from is not None):
                        calls = get_call_content(
                                content,
                                time,
                                id_sec,
                                message_from)
                        if calls is not None:
                            df = df.combine_first(calls)
                    id_sec, time, content, message_from = None, None, None, None
                prefix, event, value = get_parser_next(set_progress, parser, upload_size)
            # break, after conversation with id has been parsed
            break

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
    if (extract_values(obj, "messagetype") == ['Event/Call']):
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


def get_call_content(content, time, id_sec, message_from):
    """ takes one object from the json file and analyzes it
    
    Arguments:
        obj {dict} -- one object from the json file
        my_timezone {str} -- timezone of interest
    
    Returns:
        pd.DataFrame -- dataframe with call data
                        [ID, Start Time, End Time, Duration, Weekday, Caller Terminator]
    """

    # get datetime of event
    # unique identifier for each call to match start and end later
    call_id = re.findall('callId=\\"(\\S+)\\"', content)[0]
    # secondary id identifier for calls before mid 2019(?)

    event_category = re.findall('type=\\"(\\S+)\\"', content)[0]
    if event_category == 'started':
        try:
            calls = pd.DataFrame(data={
                'Call ID': call_id,
                'ID': id_sec,
                'Start Time': time,
                'End Time': np.nan,
                'Caller': message_from,
                'Weekday': time.weekday(),
            },
                                 index=['Call ID'])
        except pytz.exceptions.AmbiguousTimeError:
            print("Ambiguous Time Error")
            return None
    elif event_category == 'ended':
        duration = re.findall('<duration>([0-9.]+)</duration>', content)
        if len(duration) != 0:
            duration = float(duration[0])
        else:
            duration = 0
        try:
            calls = pd.DataFrame(data={
                'Call ID': call_id,
                'ID': id_sec,
                'Start Time': np.nan,
                'End Time': time,
                'Duration': duration,
                'Terminator': message_from
            },
                                 index=['Call ID'])
        except pytz.exceptions.AmbiguousTimeError:
            return None
    else:
        return
    calls.set_index('Call ID', inplace=True)
    return calls


def get_call_time(time_string, my_timezone):
    year = int(time_string[0:4])
    month = int(time_string[5:7])
    day = int(time_string[8:10])
    hour = int(time_string[11:13])
    minute = int(time_string[14:16])
    second = int(time_string[17:19])

    moment = datetime.datetime(year,
                               month,
                               day,
                               hour,
                               minute,
                               second,
                               tzinfo=datetime.timezone.utc).astimezone(
                                   pytz.timezone(my_timezone))
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
            callid_2 = index + '_2'
            date_2 = row['End Time'].date()
            try:
                starttime_2 = datetime.datetime(
                    year=date_2.year,
                    month=date_2.month,
                    day=date_2.day,
                    hour=0,
                    minute=0,
                    second=0,
                ).astimezone(pytz.timezone(my_timezone))
            except:
                continue
            endtime_2 = row['End Time']
            duration_2 = float((endtime_2 - starttime_2).seconds)
            terminator_2 = row['Terminator']

            callid_1 = index + '_1'
            starttime_1 = row['Start Time']
            date_1 = row['Start Time'].date()
            try:
                endtime_1 = datetime.datetime(
                    year=date_1.year,
                    month=date_1.month,
                    day=date_1.day,
                    hour=23,
                    minute=59,
                    second=59,
                ).astimezone(pytz.timezone(my_timezone))
            except:
                continue
            duration_1 = float((endtime_1 - starttime_1).seconds)
            caller_1 = row['Caller']

            call = pd.DataFrame(data={
                'Call ID': [callid_1, callid_2],
                'Start Time': [starttime_1, starttime_2],
                'End Time': [endtime_1, endtime_2],
                'Caller': [caller_1, np.nan],
                'Terminator': [np.nan, terminator_2],
                'Duration': [duration_1, duration_2],
                'Weekday': [starttime_1.weekday(),
                            starttime_2.weekday()],
            },
                                index=[callid_1, callid_2])
            call.set_index('Call ID', inplace=True)

            df = df.drop(index)
            df = pd.concat([df, call])

    return df