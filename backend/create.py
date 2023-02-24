import datetime
from datetime import date
from typing import Dict, cast

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly_calplot import calplot
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
    # fig_lin.write_image("images/fig_lin.png")
    # fig_bin.write_image("images/fig_bin.png")

    # fig_heat.show()
    # return all_days
    return fig_lin


def weekday_plot(df):
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
    with open("log.log", "a") as f:
        f.write(f"Week empty:\n{week}\n")
    for _, row in df.iterrows():
        try:
            day = int(cast(date, row["Start Time"]).weekday())
            value = row["Duration"]
        except ValueError:
            continue

        value = row["Duration"]
        week.iloc[day].loc['Duration'] += value if value == value else 0

    fig_bar = go.Figure()

    fig_bar.add_trace(
        go.Bar(y=week.index[::-1],
               x=week.loc[::-1, 'Duration'] / 3600,
               orientation='h'))
    fig_bar.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                          plot_bgcolor='rgb(248, 248, 255)',
                          margin=dict(l=120, r=10, t=140, b=80))
    fig_bar.update_xaxes(title_text="hours skyped", title_font={"size": 14})
    fig_bar.add_annotation(
        dict(font=dict(color='black', size=30, family='Arial'),
             x=0.12,
             y=1.2,
             showarrow=False,
             text=
             f"Your favorite skype-day is {week.loc[:,'Duration'].idxmax()}",
             textangle=0,
             xanchor='left',
             xref='paper',
             yref='paper'))
    #fig_bar.show()
    # fig_bar.write_image("images/fig_bar.png")
    return fig_bar


def calendar_plot(df):
    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["End Time"] = pd.to_datetime(df["End Time"])
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
                  colorscale="Teal",
                  years_title=True)
    return fig


def duration_plot(df):
    sum = df["Duration"].sum() / 3600

    fig = go.Figure()
    fig.add_trace(
        go.Indicator(mode="number",
                     value=round(sum, 2),
                     number={"suffix": " hours 🎉"},
                     title={"text": "Your total call time was"},
                     domain={
                         'x': [0, 1],
                         'y': [0.4, 1]
                     }))
    if sum > 100:
        fig.add_trace(
            go.Indicator(mode="number",
                         value=round(sum / 24, 2),
                         number={"suffix": " days!"},
                         title={"text": "That's equal to"},
                         domain={
                             'x': [0, 1],
                             'y': [0.1, 0.3]
                         }))
    else:
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
                      plot_bgcolor='rgb(248, 248, 255)',
                      margin=dict(l=20, r=20, t=20, b=20))
    # fig.write_image("images/fig_dur.png")
    return fig


def terminator_plot(df: pd.DataFrame, participant: Dict[str, str]):
    """
    Plot a bar chart comparing the number of "terminations" per person.
    A termination is defined as a call that was hung up by one of the participants.
    """
    counts = df["Terminator"].value_counts().sort_index()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=counts.index,
               y=counts.values,
               base="relative",
               marker=dict(color=counts.values, colorscale="rdylgn")))
    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)',
                      margin=dict(l=20, r=20, t=20, b=20),
                      title={
                          'text': "The person who's most likely to hang up...",
                          'y': 0.95,
                          'x': 0.5,
                          
                      })
    if participant is not None:
        fig.add_annotation(x=counts.argmax(),
                       y=counts.max(),
                       text="is your friend." if counts.idxmax()
                       == participant['label'] else "is you.",
                       showarrow=True,
                       arrowsize=3,
                       arrowhead=1)

    return fig


def caller_plot(df: pd.DataFrame, participant: Dict[str, str]):
    """
    Plot a bar chart comparing the number of call initiations per person.
    """
    counts = df["Caller"].value_counts().sort_index()
    print(counts)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=counts.index,
               y=counts.values,
               base="relative",
               marker=dict(color=counts.values, colorscale="rdylgn")))
    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)',
                      margin=dict(l=20, r=20, t=20, b=20),
                      title={
                          'text':
                          "The person who's most likely to start the call...",
                          'y': 0.95,
                          'x': 0.5,
                      })
    if participant is not None:
        fig.add_annotation(x=counts.argmax(),
                       y=counts.max(),
                       text="is your friend." if counts.idxmax()
                       == participant['label'] else "is you.",
                       showarrow=True,
                       arrowsize=3,
                       arrowhead=1)

    return fig


if __name__ == "__main__":
    df = pd.read_csv("test.csv")
    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["End Time"] = pd.to_datetime(df["End Time"])
    df.set_index("Call ID", inplace=True)
    fig = terminator_plot(df, {"label": "8:live:monicaabeo", "value": "test"})
    fig.show()