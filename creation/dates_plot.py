import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal


def date_graph(df):

    dates = np.array(df['Start Time'])
    # dates = dates.astype(datetime.datetime)
    durations = list(df.loc[:, 'Duration'])
    length = len(dates) - 1

    date_range = pd.date_range(dates[length], dates[0])
    all_days = pd.DataFrame(
        {
            'date': date_range,
            'call': np.zeros(date_range.shape[0]),
            'duration': np.zeros(date_range.shape[0])
        },
        columns=['date', 'call', 'duration']).set_index('date')

    for index, _ in all_days.iterrows():
        if index.date() in dates:
            all_days.at[index, 'call'] += 1

    for d, t in df.items():
        dt = datetime.datetime.combine(d, datetime.datetime.min.time())
        all_days.at[dt, 'duration'] += t
    fig_bin = px.bar(all_days, x=all_days.index, y="call")

    # fig_lin = px.line(all_days, x=all_days.index, y="duration")
    fig_lin = go.Figure()
    fig_lin.add_trace(
        go.Scatter(x=all_days.index,
                   y=all_days['duration'],
                   mode='markers',
                   name='markers'))

    fig_lin.add_trace(
        go.Scatter(
            x=all_days.index,
            y=signal.savgol_filter(
                all_days['duration'],
                65,  # window size used for filtering
                1),  # order of fitted polynomial
            mode='lines',
            line=dict(color='rgba(165,165,0,0.4)', width=10),
            name='Savitzky-Golay'))
    # fig_lin.update_yaxes(type="log")
    # fig_bin.show()
    # fig_lin.show()
    fig_lin.write_image("images/fig_lin.png")
    fig_bin.write_image("images/fig_bin.png")

    # fig_heat.show()
    # return all_days
