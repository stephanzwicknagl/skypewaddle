import pandas as pd
import datetime
import re
import numpy as np
import pytz
from rich.progress import track
from utils.console import print_step
from extraction.extract_values import extract_values


def get_times(obj, my_timezone):
    """ takes one object from the json file and analyzes it
    
    Arguments:
        obj {dict} -- one object from the json file
        my_timezone {str} -- timezone of interest
    
    Returns:
        pd.DataFrame -- dataframe with call data
                        [ID, Start Time, End Time, Duration, Weekday, Caller Terminator]
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

    event_category = re.findall('type=\\"(\S+)\\"', content)[0]
    if event_category == 'started':
        try:
            calls = pd.DataFrame(data={
                'Call ID': call_id,
                'ID': id_sec,
                'Start Time': time,
                'End Time': np.nan,
                'Caller': val_from,
                'Weekday': time.weekday(),
            },
                                 index=['Call ID'])
        except pytz.exceptions.AmbiguousTimeError:
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
                'Terminator': val_from
            },
                                 index=['Call ID'])
        except pytz.exceptions.AmbiguousTimeError:
            return None
    else:
        return
    calls.set_index('Call ID', inplace=True)
    return calls


def get_call_time(obj, my_timezone):
    time = (extract_values(obj, 'originalarrivaltime'))[0]
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

    print_step("Figuring out the days 📅")
    for index, row in track(df.iterrows(),
                            total=len(df),
                            description="Dating calls"):
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