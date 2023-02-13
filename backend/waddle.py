import os
from pathlib import Path
from utils.console import print_markdown
from extraction.get_conversations import extract_conversations
from .extraction.get_calls import get_calls
from .creation.dates_plot import date_graph
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal
# for my_timezone from location
import pytz

Path("assets/images").mkdir(parents=True, exist_ok=True)
Path("assets/data").mkdir(parents=True, exist_ok=True)


def calculate_durations(df):
    """ calculates call duration from skype times

    takes filled dataframe df 
    returns dataframe df filled with duration
    """

    for index, row in df.iterrows():
        duration = row['End Time'] - row['Start Time']
        df.loc[index, 'Duration'] = float(duration.seconds)
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
    path = "assets/data/messages.json"
    # path = "tests/test_data/mock.json"
    my_timezone = "Europe/Berlin"
    _, partner_index = extract_conversations(path)

    df = get_calls(path, partner_index, my_timezone)
    """ save df as csv """
    df.to_csv("assets/data/dataframe.csv")
    """ generates images"""
    # date_graph(df)


if __name__ == "__main__":
    main()

