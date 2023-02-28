from datetime import date
from typing import Dict, cast

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly_calplot import calplot

LOGO_URL = "https://raw.githubusercontent.com/stephanzwicknagl/skypewaddle/d29015c1bd3f859d5bcd4fd0f774553703aa65e1/assets/icon-192x192.png"

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
    fig.add_layout_image(
        dict(
            source=LOGO_URL,
            xref="paper", yref="paper",
            x=1, y=1.05,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="bottom"
        )
    )

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
    fig.add_layout_image(
        dict(
            source=LOGO_URL,
            xref="paper", yref="paper",
            x=1, y=1.05,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="bottom"
        )
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
    fig.add_trace(
        go.Indicator(mode="number",
                     value=len(df.index.unique()),
                     number={"suffix": f" calls! 📞"},
                     title={"text": "Over"},
                     domain={
                         'x': [0, 1],
                         'y': [0.1, 0.3]
                     }))

    fig.update_layout(paper_bgcolor='rgb(248, 248, 255)',
                      plot_bgcolor='rgb(248, 248, 255)')
    fig.add_layout_image(
        dict(
            source=LOGO_URL,
            xref="paper",
            yref="paper",
            x=1,
            y=1.05,
            sizex=0.2,
            sizey=0.2,
            xanchor="right",
            yanchor="bottom"))
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
    fig.add_layout_image(
        dict(
            source=LOGO_URL,
            xref="paper", yref="paper",
            x=1, y=1.05,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="bottom"
        )
    )
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
    fig.add_layout_image(
        dict(
            source=LOGO_URL,
            xref="paper", yref="paper",
            x=1, y=1.05,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="bottom"
        )
    )
    return fig
