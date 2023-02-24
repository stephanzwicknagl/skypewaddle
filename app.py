# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os

import dash_bootstrap_components as dbc
from dash import (CeleryManager, Dash, DiskcacheManager, Input, Output, dcc,
                  html)
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
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
    # some local storage
    dcc.Store(id='clientside-timezone', storage_type='memory'),
    dcc.Store(id='participant-stored', storage_type='memory'),
    dcc.Store(id='open-warn', storage_type='memory'),

    dbc.Container([
        # modals for info and warnings
        dbc.Modal(id="warn-modal", is_open=False, children=warn_content),
        dbc.Row(id="info-row", children=info_content, style={'padding': '1em 5em 0em 5em'}),
        dbc.Row(id='waddle-big-logo', children=[html.Img(src=app.get_asset_url('icon.png'),
                     alt='Skype Waddle Logo', className='logo')], style={'display': 'none'}),
        dbc.Row(id='tagline', children=[
            html.H1(children='Skype Waddle'),
            html.H3(children='Analyze your Skype habits...')
        ]),
        dbc.Row(id='user-input-step', children=[
            html.Div(
                id='data-step',
                children=[
                    html.H3(children='Upload your data to get started 🚀'),
                    dcc.Upload(id='upload-data',
                                max_size=100000000,
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ], className='upload-text'),
                                className="upload")
                ],
                style={'display': 'none'}),
            html.Div(
                id='select-participant',
                children=[
                    html.H3(children='Select your conversation partner 👥'),
                    dcc.Dropdown(id='participant_DD', searchable=False, className='dropdown')
                ],
                style={'display': 'none'}),
            html.Div(
                id='confirm-select',
                children=[
                    html.Button(
                        id='submit-participant',
                        children='Start Analyzing! 🧮',
                        n_clicks=0,
                        className='button'
                        )
                    ],
                style={'display': 'none'}),
        ],style={'display': 'none'}),
        dbc.Row(id='progress-row', children=[
            dcc.Interval(id="progress-interval", n_intervals=0, interval=500),
            dbc.Progress(id='progress-bar',
                         animated=True,
                         striped=True,
                         class_name='progress',
                         style={'display': 'none'}),
        ], style={'display': 'none'}),
        dbc.Row(dcc.Graph(id='calendar-graph'), style={'display': 'none'}),
        # dbc.Row(
            # [html.Div(id='date-time-title', style={'textAlign': 'center'})])
    ],
                  style={
                      "height": "95vh",
                      "position": "relative"
                  })
])


@app.callback(Output('waddle-big-logo', 'style'),
              Output('tagline', 'style'),
              Output('user-input-step', 'style'),
              Output('data-step', 'style'),
              Output('select-participant', 'style'),
              Output('confirm-select', 'style'), 
              Output('progress-bar', 'style'),
              Input('upload-data', 'contents'), 
              Input('participant_DD','value'),
              Input('submit-participant', 'n_clicks'),
              Input('calendar-graph', 'figure'))
def render_site_content(uploaded_data, participant_value, participant_confirmed,
                        graph_figure):
    show = {'display': 'block'}
    hide = {'display': 'none'}

    out = {
        'waddle-big-logo': show,
        'tagline': hide,
        'user-input-step': hide,
        'data-step': hide,
        'select-participant': hide,
        'confirm-select': hide,
        'progress-bar': hide,
    }

    if graph_figure is None:
        out['waddle-big-logo'] = show
        out['tagline'] = show
        out['user-input-step'] = show

    if uploaded_data is None:
        out['data-step'] = show

    if (uploaded_data is not None and
        participant_confirmed == 0):
        out['select-participant'] = show

    if (uploaded_data is not None and
        participant_value is not None and
        participant_confirmed == 0):
        out['confirm-select'] = show

    if participant_confirmed and graph_figure is None:
        out['progress-bar'] = show

    if graph_figure is not None:
        out['calendar-graph'] = show

    if graph_figure is not None:
        out['waddle-big-logo'] = hide

    if graph_figure is not None:
        out['tagline'] = hide

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


@app.callback(Output('participant-stored', 'data'),
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
    State('participant-stored', 'data'),
    background=True,
    manager=background_callback_manager,
    running=[(
        Output("progress-bar", "style"),
        {"visibility": "visible"},
        {"visibility": "hidden"},
    ),(
        Output('progress-row', 'style'),
        {'display': 'block'},
        {'display': 'none'},
    ),(
        Output('select-participant', 'style'),
        {'display': 'none'},
        {'display': 'none'},
    ),(
        Output('submit-participant', 'children'),'Analyzing... 🧮 ', 'Start Analyzing! 🧮 ',
    ),(
        Output('submit-participant', 'disabled'),True, False
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
        # return calendar_plot, False
        # duration_plot = create.duration_plot(df)
        # return duration_plot, False
        # weekday_plot = create.weekday_plot(df)
        # return weekday_plot, False
        terminator_plot = create.terminator_plot(df, participant)
        return terminator_plot, False

    raise PreventUpdate


if __name__ == '__main__':
    app.run(debug=False)