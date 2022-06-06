import pandas as pd
import datetime
import re
import numpy as np
import pytz
from rich.progress import track
from utils.console import print_step
from extraction.extract_values import extract_values


def get_times(obj, my_timezone):
    """ takes an object from the json file and analyzes it
    
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

    event_category = re.findall('type=\\"(\S+)\\"', content)[0]
    if event_category == 'started':
        try:
            calls = pd.DataFrame(data={
                'Call ID':
                call_id,
                'ID':
                id_sec,
                'Start Time':
                time,
                'End Time':
                np.nan,
                'Caller':
                val_from,
                'Weekday':
                time.weekday(),
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
                'Call ID':
                call_id,
                'ID':
                id_sec,
                'Start Time':
                np.nan,
                'End Time':
                time,
                'Duration':
                duration,
                'Terminator':
                val_from
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
    print_step("Figuring out the days 📅")
    for index, row in track(df.iterrows(),
                            total=len(df),
                            description="Dating calls"):
        if row['Start Time'].date() != row['End Time'].date():
            call_id_new = index + '_2'
            date_new = row['End Time'].date()
            try:
                start_time_new = datetime.datetime(
                    year=date_new.year,
                    month=date_new.month,
                    day=date_new.day,
                    hour=0,
                    minute=0,
                    second=0,
                ).astimezone(
                    pytz.timezone(my_timezone))
            except:
                continue
            end_time_new = row['End Time']
            duration_new = float((end_time_new - start_time_new).seconds)
            terminator_new = row['Terminator']

            call_id_pre = index + '_1'
            start_time_pre = row['Start Time']
            date_pre = row['Start Time'].date()
            try:
                end_time_pre = datetime.datetime(
                    year=date_pre.year,
                    month=date_pre.month,
                    day=date_pre.day,
                    hour=23,
                    minute=59,
                    second=59,
                ).astimezone(pytz.timezone(my_timezone))
            except:
                continue
            duration_pre = row['Duration'] - duration_new
            caller_pre = row['Caller']

            call = pd.DataFrame(data={
                'Call ID': [call_id_pre, call_id_new],
                'Start Time': [start_time_pre, start_time_new],
                'End Time': [end_time_pre, end_time_new],
                'Caller': [caller_pre, np.nan],
                'Terminator': [np.nan, terminator_new],
                'Duration': [duration_pre, duration_new],
                'Weekday': [start_time_pre.weekday(), start_time_new.weekday()],
            },
                                index=[call_id_pre, call_id_new])
            call.set_index('Call ID', inplace=True)

            df = df.drop(index)
            df = df.append(call)

    return df