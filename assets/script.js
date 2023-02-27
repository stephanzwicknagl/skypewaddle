window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        run_on_participant_select: function(participant_submitted, participant_options, participant_value, upload_contents, upload_filename) {
            clientside_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            async function main(){
                let my_js_namespace = { participant_submitted : participant_submitted,
                                        participant_options : participant_options,
                                        participant_value : participant_value,
                                        upload_contents : upload_contents,
                                        upload_filename : upload_filename,
                                        timezone : clientside_timezone
                                     };
                let pyodide = await loadPyodide();
                pyodide.registerJsModule("my_js_namespace", my_js_namespace);
                await pyodide.loadPackage("pytz")
                await pyodide.loadPackage("numpy")
                await pyodide.loadPackage("pandas")
                await pyodide.loadPackage("micropip");
                const micropip = pyodide.pyimport("micropip");
                await micropip.install('plotly');
                await micropip.install('plotly-calplot');
                pyodide.runPython(`
from my_js_namespace import participant_submitted, participant_options, participant_value, upload_contents, upload_filename, timezone

from pytz import UnknownTimeZoneError
from pytz import timezone as pytztimezone
import sys

import datetime
import re

import numpy as np
import pandas as pd
import pytz

import base64
import tarfile
import io
import json

from datetime import date
from typing import Dict, cast

import plotly.graph_objects as go
from plotly_calplot import calplot


def weekday_plot(df: pd.DataFrame) -> go.Figure:
    week = pd.DataFrame(
        {
            'Day': [
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday"
            ],
            'Duration':
            np.zeros(7),
            'Avg':
            np.zeros(7)
        },
        columns=['Day', 'Duration', 'Avg']).set_index("Day")
    for _, row in df.iterrows():
        try:
            day = int(cast(date, row["Start Time"]).weekday())
            value = row["Duration"]
        except ValueError:
            continue

        value = row["Duration"]
        week.iloc[day].loc['Duration'] += value if value == value else 0

    fig = go.Figure()

    unit = "hours" if week.loc[:, 'Duration'].sum() > 3600 else "minutes"
    week.loc[:, 'Duration'] = week.loc[:, 'Duration'] / 3600 if unit == "hours" else week.loc[:, 'Duration'] / 60

    fig.add_trace(
        go.Bar(y=week.index[::-1],
               x=week.loc[::-1, 'Duration'],
               orientation='h'))
    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)',
                      title=f"Your favorite skype-day is {week.loc[:,'Duration'].idxmax()}")
    fig.update_xaxes(title_text=f"{unit} skyped", title_font={"size": 14})

    return fig


def calendar_plot(df: pd.DataFrame) -> go.Figure:
    start_date = df["Start Time"].min().date()
    end_date = df["Start Time"].max().date()

    # sum of duration per day in hours
    day_durations = df.groupby(pd.Grouper(key="Start Time",
                                          freq="D"))["Duration"].sum() / 3600
    df = pd.DataFrame({
        "ds": pd.date_range(start_date, end_date),
        "value": day_durations,
    })

    fig = calplot(df,
                  x="ds",
                  y="value",
                  name="Call Duration in Hours",
                  gap=0,
                  month_lines_width=3,
                  month_lines_color="#eeeeff",
                  colorscale="Teal",
                  years_title=True)
    fig.update_layout(
        paper_bgcolor='rgb(248, 248, 255)',
        plot_bgcolor='rgb(248, 248, 255)',
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig


def duration_plot(df: pd.DataFrame) -> go.Figure:
    sum = df["Duration"].sum()
    unit = "hours" if sum > 3600 else "minutes"
    sum = sum / 3600 if sum > 3600 else sum / 60

    fig = go.Figure()
    fig.add_trace(
        go.Indicator(mode="number",
                     value=round(sum, 2),
                     number={"suffix": f" {unit} 🎉"},
                     title={"text": "Your total call time was"},
                     domain={
                         'x': [0, 1],
                         'y': [0.4, 1]
                     }))
    if sum > 100 and unit == "hours":
        fig.add_trace(
            go.Indicator(mode="number",
                         value=round(sum / 24, 2),
                         number={"suffix": " days!"},
                         title={"text": "That's equal to"},
                         domain={
                             'x': [0, 1],
                             'y': [0.1, 0.3]
                         }))
    if sum < 100 and unit == "hours":
        fig.add_trace(
            go.Indicator(mode="number",
                         value=round(sum / 1.5, 2),
                         number={"suffix": " Shreks!"},
                         title={"text": "That's equal to"},
                         domain={
                             'x': [0, 1],
                             'y': [0.1, 0.3]
                         }))
    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)')

    return fig


def terminator_plot(df: pd.DataFrame, participant: Dict[str, str])  -> go.Figure:
    """
    Plot a bar chart comparing the number of "terminations" per person.
    A termination is defined as a call that was hung up by one of the participants.
    """
    counts = df["Terminator"].value_counts().sort_index()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=counts.index,
               y=counts.values/counts.sum(),
               base="relative",
               marker=dict(color=counts.values, colorscale="rdylgn")))
    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)',
                      title={
                          'text': "The person who's most likely to hang up...",
                          'y': 0.95,
                          'x': 0.5,
                          
                      })
    if participant is not None:
        text_str = "is your friend." if counts.idxmax() == participant['label'] else "is you."
        fig.add_annotation(
                       x=counts.argmax(),
                       y=counts.max()/counts.sum(),
                       text= text_str,
                       showarrow=True,
                       arrowsize=3,
                       arrowhead=1)

    return fig


def caller_plot(df: pd.DataFrame, participant: Dict[str, str]) -> go.Figure:
    """
    Plot a bar chart comparing the number of call initiations per person.
    """
    counts = df["Caller"].value_counts().sort_index()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=counts.index,
               y=counts.values/counts.sum(),
               base="relative",
               marker=dict(color=counts.values, colorscale="rdylgn")))
    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)',
                      title={
                          'text':
                          "The person who's most likely to start the call...",
                          'y': 0.95,
                          'x': 0.5,
                      })
    if participant is not None:
        text_str = "is your friend." if counts.idxmax() == participant['label'] else "is you."
        fig.add_annotation(x=counts.argmax(),
                       y=counts.max()/counts.sum(),
                       text=text_str,
                       showarrow=True,
                       arrowsize=3,
                       arrowhead=1)
        
    return fig


def read_conversations_from_file(contents, filename):

    _, content_string = contents.split(',')
    decoded_data = base64.b64decode(content_string)

    data = {}
    if filename.endswith('.json'):
        data = json.load(io.BytesIO(decoded_data))
    elif filename.endswith('.tar'):
        buffer = io.BytesIO(decoded_data)
        tar = tarfile.open(fileobj=buffer, mode="r")

        file = next(filter(lambda tar_element: tar_element.name == "messages.json", list(tar.getmembers())))
        decoded_data = tar.extractfile(file)

        if decoded_data is not None:
            data = json.load(decoded_data)
        else:
            print("decoded_data is None")
    else:
        print("unknown file type")

    return data['conversations'] if 'conversations' in data else None


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

    idxs = {}
    for i in range(0, len(conversations)):
        partner = conversations[i]['id']
        if re.search('.skype', partner) is None:
            idxs[partner] = i
    return idxs


def get_calls(conversations, partner_index, my_timezone):
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
        # set_progress((str(i), str(len(messages))))
        # not-calls are ignored
        if not is_call(obj):
            continue

        # extract call data
        try:
            calls = get_times(obj, my_timezone)
        except IndexError:
            raise ValueError
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
    call_id = re.findall('callId=\\"(\\S+)\\"', content)[0]
    # secondary id identifier for calls before mid 2019(?)
    id_sec = extract_values(obj, 'id')[0]

    event_category = re.findall('type=\\"(\\S+)\\"', content)[0]
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

if timezone is None:
    timezone = 'UTC'
try:
    pytztimezone(timezone)
except UnknownTimeZoneError:
    timezone = 'UTC'
print(timezone)

df = pd.DataFrame()
if (participant_value is not None and
    participant_submitted > 0):
    conversations = read_conversations_from_file(upload_contents, upload_filename)
    try:
        df = get_calls(conversations, participant_value,
                        timezone)
    except ValueError:
        plots = None
        sys.exit()
    print(df)
                `);
                if (upload_contents !== null) {
                    return pyodide.globals.get('df');
                }
                else {
                    return null
                }
            }
            return main();
            // new Worker , onmessage, onerror
        }
    }
});