# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import pandas as pd
from backend import extract
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import os
import dash_bootstrap_components as dbc
from dash import DiskcacheManager, CeleryManager, Input, Output, html
from dash_iconify import DashIconify


if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
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

app.layout = html.Div(children=[
    dbc.Container([
        dbc.Row([
            DashIconify(icon="material-symbols:info", className="info", style={"color": "#00aff0"})
        ]),

        dbc.Row([
            html.H1(children='Skype Waddle', style={'textAlign': 'center'}),
            html.H3(children='Analyze your Skype habits...', style={'textAlign': 'center'})
        ]),

        dbc.Row([
            html.Div(id='data-step',
                     children=[
                         'Upload your data to get started 🚀',
                         dcc.Upload(id='upload-data',
                                    children=html.Div([
                                        'Drag and Drop or ',
                                        html.A('Select Files')
                                    ]),
                                    className="upload")
                     ],
                     style={'display': 'none', 'textAlign': 'center'}),
            html.Div(
                id='select-participant',
                children=[
                    html.H3(children='Select your conversation partner 👥 ', style={"textAlign": "center"}),
                    dcc.Dropdown(id='participant_DD', className='dropdown')
                ],
                style={'display': 'none'})]),
        dbc.Row([
            html.Div(id='confirm-select',
                     children=[
                         html.Button('Start Analyzing! 🧮 ',
                                     id='submit-participant',
                                     n_clicks=0,
                                     className='button',
                                     style={'display': 'block', 'margin': 'auto'})
                     ],
                     style={'display': 'none'}),
            html.Div(id='test')]),
        dbc.Row([
            dcc.Interval(id="progress-interval", n_intervals=0, interval=500),
            dbc.Progress(id='progress-bar',
                          animated=True,
                          striped=True,
                          class_name='progress',
                          style={'display': 'none'}),
            dcc.Graph(id='weekday-graph', style={'display': 'none'}),
        ], justify="center", align="center")
    ],  style={"height": "100vh", "position": "relative"})
])

@app.callback(Output('data-step', 'style'),
              Output('select-participant', 'style'),
              Output('confirm-select', 'style'),
              Output('progress-bar', 'style'),
              Output('weekday-graph', 'style'),
              Input('upload-data', 'contents'),
              Input('participant_DD', 'value'),
              Input('submit-participant', 'n_clicks'))
def render_site_content(contents, participant_value, n_clicks):
    show = {'display': 'block'}
    hide = {'display': 'none'}

    out = {'data-step': hide,
           'select-participant': hide,
           'confirm-select': hide,
           'progress-bar': hide,
           'weekday-graph': hide
    }

    if contents is not None:
        out['select-participant'] = show
        if participant_value is not None:
            out['confirm-select'] = show
    else:
        out['data-step'] = show

    if n_clicks:
        out['progress-bar'] = show

    return [out[k] for k in out]

@app.callback(Output('participant_DD', 'options'),
              Input('upload-data', 'contents'))
def on_upload(contents):
    if contents is not None:
        participants = extract.extract_conversations(contents)
        options = [{'label': p, 'value': idx} for idx, p in enumerate(participants)]
        return options
    raise PreventUpdate


@app.callback(Output('test','children'),
              Input('submit-participant', 'n_clicks'),
              State('participant_DD', 'value'),
              State('upload-data', 'contents'),
              background=True, manager=background_callback_manager,
              running=[(
                    Output("progress-bar", "style"),
                    {"visibility": "visible"},
                    {"visibility": "hidden"},
                )],
              progress=[Output("progress-bar", "value"), Output("progress-bar", "max")],
              prevent_initial_call=True)
def on_participant_select(update_progress, n_clicks, value, contents):
    if value is not None and n_clicks > 0:
        # call function extraction.get_calls asynchronously
        df = extract.get_calls(update_progress, contents, value, "Europe/Berlin")
        children = [
            html.H3(children='First few lines of partners'),
            html.Div(str(df.head()))
        ]
        return children
    raise PreventUpdate

if __name__ == '__main__':
    app.run(debug=True)