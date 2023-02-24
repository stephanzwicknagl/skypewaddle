# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os

import dash_bootstrap_components as dbc
import pandas as pd
from dash import (CeleryManager, Dash, DiskcacheManager, Input, Output, dcc,
                  html)
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from pytz import UnknownTimeZoneError
from pytz import timezone as pytztimezone

from backend import create, extract, utils
from frontend.info import info_content
from frontend.warn import warn_content

if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(__name__,
                        broker=os.environ['REDIS_URL'],
                        backend=os.environ['REDIS_URL'])
    background_callback_manager = CeleryManager(celery_app)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

app = Dash(__name__,
           title="skype waddle",
           update_title="Loading...",
           external_stylesheets=[dbc.themes.LUMEN])

server = app.server

app.clientside_callback(
    """
    function(n_clicks) { 
        const obj = new Object();         
        obj.clientside_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        return obj;
    }
    """,
    Output('clientside-timezone', 'data'),
    Input('submit-participant', 'n_clicks'),
)

app.layout = html.Div(children=[
    dcc.Store(id='clientside-timezone', storage_type='memory'),
    dcc.Store(id='participant-store', storage_type='memory'),
    dcc.Store(id='open-warn', storage_type='memory'),
    dbc.Container([
        warn_content,
        dbc.Row(info_content, style={'padding': '1em 5em 0em 5em'}),
        dbc.Row(html.Img(src=app.get_asset_url('icon.png'),
                     className='logo',
                     alt='Skype Waddle Logo'), style={'padding': '0em 5em 0em 5em'}),
        dbc.Row([
            html.H1(children='Skype Waddle', style={'textAlign': 'center'}),
            html.H3(children='Analyze your Skype habits...',
                    style={'textAlign': 'center'})
        ]),
        dbc.Row([
            html.Div(id='data-step',
                     children=[
                         'Upload your data to get started 🚀',
                         dcc.Upload(id='upload-data',
                                    max_size=100000000,
                                    children=html.Div([
                                        'Drag and Drop or ',
                                        html.A('Select Files')
                                    ], style={'textAlign': 'center', 'padding':'1em'}),
                                    className="upload")
                     ],
                     style={
                         'display': 'none',
                         'textAlign': 'center'
                     }),
            html.Div(
                id='select-participant',
                children=[
                    html.H3(children='Select your conversation partner 👥 ',
                            style={"textAlign": "center"}),
                    dcc.Dropdown(id='participant_DD', className='dropdown')
                ],
                style={'display': 'none'})
        ]),
        dbc.Row([
            html.Div(id='confirm-select',
                     children=[
                         html.Button('Start Analyzing! 🧮 ',
                                     id='submit-participant',
                                     n_clicks=0,
                                     className='button',
                                     style={
                                         'display': 'block',
                                         'margin': 'auto'
                                     })
                     ],
                     style={'display': 'none'}),
            html.Div(id='test')
        ]),
        dbc.Row([
            dcc.Interval(id="progress-interval", n_intervals=0, interval=500),
            dbc.Progress(id='progress-bar',
                         animated=True,
                         striped=True,
                         class_name='progress',
                         style={'display': 'none'}),
            dcc.Graph(id='calendar-graph', style={'display': 'none'}),
        ],
                justify="center",
                align="center"),
        # dbc.Row(
            # [html.Div(id='date-time-title', style={'textAlign': 'center'})])
    ],
                  style={
                      "height": "100vh",
                      "position": "relative"
                  })
])


@app.callback(Output('data-step', 'style'),
              Output('select-participant', 'style'),
              Output('confirm-select', 'style'), 
              Output('progress-bar', 'style'),
              Output('calendar-graph', 'style'),
              Input('upload-data', 'contents'), 
              Input('participant_DD','value'),
              Input('submit-participant', 'n_clicks'),
              Input('calendar-graph', 'figure'))
def render_site_content(uploaded_data, participant_value, n_clicks,
                        weekday_figure):
    show = {'display': 'block'}
    hide = {'display': 'none'}

    out = {
        'data-step': hide,
        'select-participant': hide,
        'confirm-select': hide,
        'progress-bar': hide,
        'calendar-graph': hide
    }

    if uploaded_data is not None and weekday_figure is None:
        out['select-participant'] = show
        if participant_value is not None:
            out['confirm-select'] = show
    else:
        out['data-step'] = show

    if n_clicks and weekday_figure is None:
        out['progress-bar'] = show

    if weekday_figure is not None:
        out['calendar-graph'] = show

    return [out[k] for k in out]


@app.callback(Output('participant_DD', 'options'),
              Input('upload-data', 'contents'), State('upload-data',
                                                      'filename'))
def on_upload(contents, filename):
    if contents is not None:
        conversations = utils.read_conversations_from_file(contents, filename)
        participants = extract.extract_conversations(conversations)
        options = [{
            'label': p,
            'value': idx
        } for idx, p in enumerate(participants)]
        return options
    raise PreventUpdate


@app.callback(
    Output("info-modal", "is_open"),
    [Input("info-open", "n_clicks"),
     Input("info-close", "n_clicks")],
    [State("info-modal", "is_open")],
)
def toggle_info_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("warn-modal", "is_open"),
    [Input("warn-close", "n_clicks"),
     Input('open-warn', 'data')],
    [State("warn-modal", "is_open")])
def toggle_warn_modal(n_clicks, open_warn, is_open):
    if n_clicks or open_warn:
        return not is_open
    return is_open


@app.callback(Output('participant-store', 'data'),
              Input('submit-participant', 'n_clicks'),
              State('participant_DD', 'options'),
              State('participant_DD', 'value'))
def save_participant_select(n_clicks, options, value):
    if n_clicks:
        return options[value]
    raise PreventUpdate


@app.callback(
    Output('calendar-graph', 'figure'),
    Output('open-warn', 'data'),
    Input('submit-participant', 'n_clicks'),
    State('participant_DD', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('clientside-timezone', 'data'),
    State('participant-store', 'data'),
    background=True,
    manager=background_callback_manager,
    running=[(
        Output("progress-bar", "style"),
        {
            "visibility": "visible"
        },
        {
            "visibility": "hidden"
        },
    )],
    progress=[Output("progress-bar", "value"),
              Output("progress-bar", "max")],
    prevent_initial_call=True)
def on_participant_select(update_progress, n_clicks, value, contents, filename,
                          timezone, participant):
    # check if the timezone is valid:
    try:
        pytztimezone(timezone['clientside_timezone'])
    except UnknownTimeZoneError:
        timezone['clientside_timezone'] = 'UTC'


    if value is not None and n_clicks > 0:
        conversations = utils.read_conversations_from_file(contents, filename)
        try:
            df = extract.get_calls(update_progress, conversations, value,
                               timezone['clientside_timezone'])
        except ValueError:
            return None, True
        # get type of weekday column in df
        df.to_csv("test.csv")

        # calendar_plot = create.calendar_plot(df)
        # return calendar_plot
        # duration_plot = create.duration_plot(df)
        # return duration_plot
        # weekday_plot = create.weekday_plot(df)
        # return weekday_plot
        terminator_plot = create.terminator_plot(df, participant)
        return terminator_plot

    raise PreventUpdate


if __name__ == '__main__':
    app.run(debug=True)