#for print style
#import os

import json
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal




# Opening JSON file
f = open('data/31-03.json',"r",encoding='utf-8')

# returns JSON object as
# a dictionary
data = json.load(f)

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

def extract_durations(obj):
    arr = []
    days = 0
    for item in obj:
        beg_duration = item.find("<duration>")
        end_duration= item.find("</duration>")
        if (beg_duration!=-1 & end_duration !=-1):
            duration = float(item[beg_duration+10:end_duration])
            days += duration
            arr.append(duration)
    return arr, days/60/60/24

def extract_call_date(obj, calls):
    for item in obj:
        duration=0
        if(is_call(item)):
            j = extract_values(item, 'originalarrivaltime')
            year  = int(j[0][0:4])
            month = int(j[0][5:7])
            day   = int(j[0][8:10])
            
            j = extract_values(item, "content")
            beg_duration = j[0].find("<duration>")
            end_duration = j[0].find("</duration>")
            if (beg_duration != -1 & end_duration != -1):
                duration = float(j[0][beg_duration+10:end_duration])/60/60
            if datetime.date(year, month, day) in calls:
                buffer = calls[datetime.date(year, month, day)]
                del calls[datetime.date(year, month, day)]
                calls[datetime.date(year, month, day)]=buffer+duration
            else:
                calls[datetime.date(year, month, day)] = duration


def is_call(obj):
    if(extract_values(obj, "messagetype") == ['Event/Call']):
        return True
    return False

def date_graph(calls):
    dates = list(calls.keys())
    durations = list(calls.values())
    length = len(dates)-1
    
    a = pd.date_range(dates[length], dates[0])
    all_days = pd.DataFrame({
        'date': a,
        'call': np.zeros(a.shape[0]),
        'duration' : np.zeros(a.shape[0])
    }, columns=['date', 'call', 'duration']).set_index("date")
    
    for index,row in all_days.iterrows():
        if index.date() in dates:
            all_days.at[index,'call']+=1

    for d,t in calls.items():
        dt=datetime.datetime.combine(d, datetime.datetime.min.time())
        all_days.at[dt,'duration']+=t
    fig_bin  = px.bar(all_days, x=all_days.index, y="call")
    
    #fig_lin = px.line(all_days, x=all_days.index, y="duration")
    fig_lin = go.Figure()
    fig_lin.add_trace(go.Scatter(x=all_days.index, y=all_days['duration'],
                             mode='markers',
                             name='markers'))

    fig_lin.add_trace(go.Scatter(x=all_days.index,
                            y=signal.savgol_filter(all_days['duration'],
                                                65,  # window size used for filtering
                                                1),  # order of fitted polynomial
                            mode='lines',
                                 line=dict(color='rgba(165,165,0,0.4)', width=10 ),
                            name='Savitzky-Golay'
    ))
    #fig_lin.update_yaxes(type="log")
    #fig_bin.show()
    fig_lin.show()
    #fig_heat.show()
    return all_days

def week_avg(df):
    week = pd.DataFrame({
        'day': np.arange(1,8),
        'dings': np.zeros(7),
        'duration': np.zeros(7),
        'avg': np.zeros(7)
    }, columns=['day', 'dings', 'duration', 'avg']).set_index("day")
    for ind,row in df.iterrows():
        week.loc[ind.isoweekday(), 'duration'] += row.loc['duration']
        week.loc[ind.isoweekday(), 'dings'] += 1
    week.loc[:,'avg']=week.loc[:,'duration']/week.loc[:,'dings']

    weekdays_aux = ["Sunday", "Saturday", "Friday", "Thursday", "Wednesday", "Tuesday", "Monday"]
    fig_bar=go.Figure()
    
    fig_bar.add_trace(go.Bar(   
                y=weekdays_aux,
                x=week.iloc[::-1,2],
                orientation='h'
    ))
    fig_bar.update_layout(
        paper_bgcolor='rgb(248, 248, 255)',
        plot_bgcolor='rgb(248, 248, 255)',
        margin=dict(l=120, r=10, t=140, b=80)
    )
    fig_bar.show()

    print(week.max())







     

        


def get_duration():
    """extract message content into array"""
    #begin recursion
    message_content=extract_values(data, "content")

    """extract call durations"""
    durations, days = extract_durations(message_content)
    #print(durations)
    print("Number of calls: ",len(durations))
    print("Total skype-time in days: ",days)
    print("That is " + str(round(days*24,2)) + " hours!")
    print("     or " + str(round(days*24*60)) + " minutes!")
    print("        " + str(round(days*24*60*60)) + " seconds!")
    # Closing file




#initialize files
calls=dict([])

#extract MessageList as array
#message_content[0] is most recent message
message_content = data['conversations'][0]['MessageList']


extract_call_date(message_content, calls)
all_days=date_graph(calls)
week_avg(all_days)
f.close()
