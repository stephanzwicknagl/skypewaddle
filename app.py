# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import json
import os

import dash_bootstrap_components as dbc
from dash import (CeleryManager, Dash, DiskcacheManager, Input, Output, dcc,
                  html)
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.io as pio
from pytz import UnknownTimeZoneError
from pytz import timezone as pytztimezone

from backend import create, extract, utils
from frontend.download import download_content
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
           external_stylesheets=[dbc.themes.LUMEN],
           background_callback_manager=background_callback_manager)

server = app.server

app.clientside_callback(
    """
    function(data) { 
        const obj = new Object();         
        obj.clientside_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        return obj;
    }
    """,
    Output('clientside-timezone', 'data'),
    [Input('submit-participant', 'n_clicks'),
     Input('url', 'pathname')],
)

app.clientside_callback(
    """
    function(data) {
        console.log(data);
        return null;
    }""",
    Output('data2', 'data'),
    Input('data', 'data'),
)

app.layout = html.Div(children=[
    # some local storage
    dcc.Store(id='clientside-timezone', storage_type='memory'),
    dcc.Store(id='data', storage_type='memory'),
    dcc.Store(id='data2', storage_type='memory'),
    dcc.Store(id='open-warn', storage_type='memory'),
    dcc.Store(id='plots', storage_type='local'),
    # url for relaunching app
    dcc.Location(id='url', refresh=True),

    dbc.Container([
        # modals for info and warnings
        dbc.Modal(id="warn-modal", is_open=False, children=warn_content),
        dbc.Row(id="info-row",
                children= info_content, style={'padding': '1em 5em 0em 5em'}),
        # logo in header
        dbc.Row(id='App-logo', children=[
            html.Div(id='waddle-big-logo',
                     children=[html.Img(src=app.get_asset_url('icon.png'),
                               alt='Skype Waddle Logo', className='logo-big')],
                     style={'display': 'none'}),
            html.Div(id='waddle-small-logo',
                     children=[html.Img(src=app.get_asset_url('icon.png'),
                               alt='Skype Waddle Logo', className='logo-small')],
                     n_clicks=0,
                     style={'display': 'none'})
                     ], style={'padding': '0em'}),
        # main content
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
                    # make sure dropdown doesn't cut off at the bottom of the page
                    dcc.Dropdown(id='participant_DD', searchable=False, className='dropdown'),
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
        ],style={'display': 'none'}),
        dbc.Row(id='graph-row', style={'display': 'none'}),
        dbc.Row(id='download-step', children=download_content, style={'display': 'none'}),
    ],
    style={
        "height": "90vh",
        "position": "relative"
    })
])


@app.callback(Output('waddle-big-logo', 'style'),
              Output('waddle-small-logo', 'style'),
              Output('tagline', 'style'),
              Output('user-input-step', 'style'),
              Output('data-step', 'style'),
              Output('select-participant', 'style'),
              Output('confirm-select', 'style'),
              Output('progress-bar', 'style'),
              Output('graph-row', 'style'),
              Output('download-step', 'style'),
              Input('upload-data', 'contents'),
              Input('participant_DD','value'),
              Input('submit-participant', 'n_clicks'),
              Input('graph-row', 'children'),
              Input('plots', 'data'),
)
def render_site_content(uploaded_data, participant_value, participant_confirmed,
                        graph_figure, plots_storage):
    show = {'display': 'block'}
    hide = {'display': 'none'}

    out = {
        'waddle-big-logo': show,
        'waddle-small-logo': hide,
        'tagline': hide,
        'user-input-step': hide,
        'data-step': hide,
        'select-participant': hide,
        'confirm-select': hide,
        'progress-bar': hide,
        'graph-row': hide,
        'download-step': hide,
    }

    if graph_figure is None and plots_storage is None:
        out['waddle-big-logo'] = show
        out['tagline'] = show
        out['user-input-step'] = show

    if uploaded_data is None and plots_storage is None:
        out['data-step'] = show

    if (uploaded_data is not None and
        participant_confirmed == 0 and
        plots_storage is None):
        out['select-participant'] = show

    if (uploaded_data is not None and
        participant_value is not None and
        participant_confirmed == 0 and
        plots_storage is None):
        out['confirm-select'] = show

    if (participant_confirmed and
        graph_figure is None and
        plots_storage is None):
        out['progress-bar'] = show

    if (graph_figure is not None or
        plots_storage is not None):
        out['graph-row'] = show

    if (graph_figure is not None or
        plots_storage is not None):
        out['waddle-big-logo'] = hide

    if (graph_figure is not None or
        plots_storage is not None):
        out['waddle-small-logo'] = show

    if (graph_figure is not None or
        plots_storage is not None):
        out['tagline'] = hide

    if (graph_figure is not None or
        plots_storage is not None):
        out['download-step'] = show

    return [out[k] for k in out]


@app.callback(Output('participant_DD', 'options'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'))
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
    Input("info-open", "n_clicks"),
    Input("info-close", "n_clicks"),
    State("info-modal", "is_open"),
)
def toggle_info_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("warn-modal", "is_open"),
    Input('open-warn', 'data'),
    State("warn-modal", "is_open"),
)
def toggle_warn_modal(open_warn, is_open):
    if open_warn:
        return not is_open
    return is_open


@app.callback(
    Output('graph-row', 'children'),
    Output('plots', 'data'),
    Output('open-warn', 'data'),
    Input('submit-participant', 'n_clicks'),
    Input('plots', 'data'),
    State('participant_DD', 'options'),
    State('participant_DD', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('clientside-timezone', 'data'),
    background=True,
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
def on_participant_select(update_progress, participant_submitted, plots_storage, participant_options,
                          participant_value, upload_contents, upload_filename,
                          timezone):
    if timezone is None:
        timezone = {'clientside_timezone': 'UTC'}
    try:
        pytztimezone(timezone['clientside_timezone'])
    except UnknownTimeZoneError:
        timezone['clientside_timezone'] = 'UTC'


    if ((participant_value is not None and
        participant_submitted > 0) or
        plots_storage is not None):
        if plots_storage is None:
            conversations = utils.read_conversations_from_file(upload_contents, upload_filename)
            # try:
            df = extract.get_calls(update_progress, conversations, participant_value,
                                timezone['clientside_timezone'])
            # except ValueError:
            #     return None, None, True
            plots ={
                'duration-plot': create.duration_plot(df),
                'weekday-plot': create.weekday_plot(df),
                'calendar-plot': create.calendar_plot(df),
                'caller-plot': create.caller_plot(df, participant_options[participant_value]),
                'terminator-plot': create.terminator_plot(df, participant_options[participant_value]),
            }
        else:
            plots = plots_storage
        tabs = dbc.Tabs(
            [
                dbc.Tab(label="Duration", tab_id="duration-plot", children=utils.make_tab(plots['duration-plot'])),
                dbc.Tab(label="Weekday", tab_id="weekday-plot", children=utils.make_tab(plots['weekday-plot'])),
                dbc.Tab(label="Calendar", tab_id="calendar-plot", children=utils.make_tab(plots['calendar-plot'])),
                dbc.Tab(label="Call starter", tab_id="caller-plot", children=utils.make_tab(plots['caller-plot'])),
                dbc.Tab(label="Call ender", tab_id="terminator-plot", children=utils.make_tab(plots['terminator-plot'])),
            ]
        )

        return tabs, plots, False

    raise PreventUpdate

@app.callback(
    Output('download-duration-plot', 'data'),
    Input('download-button', 'n_clicks'),
    State('plots', 'data'),
    prevent_initial_call=True,
)
def download_duration_data(download_click, plots_storage):
    if download_click > 0:
        fig = pio.from_json(json.dumps(plots_storage['duration-plot']))
        img_bytes = fig.to_image(format="png", scale=10)
        img_name = "waddle-duration.png"
        return dcc.send_bytes(img_bytes, img_name)
    raise PreventUpdate

@app.callback(
    Output('download-weekday-plot', 'data'),
    Input('download-button', 'n_clicks'),
    State('plots', 'data'),
    prevent_initial_call=True,
)
def download_weekday_data(download_click, plots_storage):
    if download_click > 0:
        fig = pio.from_json(json.dumps(plots_storage['weekday-plot']))
        img_bytes = fig.to_image(format="png", scale=10)
        img_name = "waddle-weekday.png"
        return dcc.send_bytes(img_bytes, img_name)
    raise PreventUpdate

@app.callback(
    Output('download-calendar-plot', 'data'),
    Input('download-button', 'n_clicks'),
    State('plots', 'data'),
    prevent_initial_call=True,
)
def download_calendar_data(download_click, plots_storage):
    if download_click > 0:
        fig = pio.from_json(json.dumps(plots_storage['calendar-plot']))
        img_bytes = fig.to_image(format="png", scale=10)
        img_name = "waddle-year.png"
        return dcc.send_bytes(img_bytes, img_name)
    raise PreventUpdate

@app.callback(
    Output('download-caller-plot', 'data'),
    Input('download-button', 'n_clicks'),
    State('plots', 'data'),
    prevent_initial_call=True,
)
def download_caller_data(download_click, plots_storage):
    if download_click > 0:
        fig = pio.from_json(json.dumps(plots_storage['caller-plot']))
        img_bytes = fig.to_image(format="png", scale=10)
        img_name = "waddle-caller.png"
        return dcc.send_bytes(img_bytes, img_name)
    raise PreventUpdate

@app.callback(
    Output('download-terminator-plot', 'data'),
    Input('download-button', 'n_clicks'),
    State('plots', 'data'),
    prevent_initial_call=True,
)
def download_terminator_data(download_click, plots_storage):
    if download_click > 0:
        fig = pio.from_json(json.dumps(plots_storage['terminator-plot']))
        img_bytes = fig.to_image(format="png", scale=10)
        img_name = "waddle-callender.png"
        return dcc.send_bytes(img_bytes, img_name)
    raise PreventUpdate

@app.callback(
    Output('download-sample-data', 'data'),
    Input('sample-data-button', 'n_clicks'),
    prevent_initial_call=True,
)
def download_sample_data(download_click):
    if download_click > 0:
        return dcc.send_file("./tests/test_data/TestData.tar")
    raise PreventUpdate

@app.callback(
    Output("url", "href"),
    Output('plots', 'clear_data'),
    Input("waddle-small-logo", "n_clicks"),
    Input("warn-close", "n_clicks"),
    prevent_initial_call=True,
)
def reload_data(app_logo, warn_close):
    if app_logo or warn_close:
        return "/", True
    raise PreventUpdate

@app.callback(
    Output('data', 'data'),
    Input('waddle-big-logo', 'children'),
    State('data', 'data')
)
def console_log(children, data):
    if children is not None and data is None:
        printstr = r"""
                         __                          __
          _      _____  / /________  ____ ___  ___  / /
         | | /| / / _ \/ / ___/ __ \/ __ `__ \/ _ \/ / 
         | |/ |/ /  __/ / /__/ /_/ / / / / / /  __/_/  
         |__/|__/\___/_/\___/\____/_/ /_/ /_/\___(_)   
                                             
  _ _ _                _         _                                ___ 
 | (_) |_____  __ __ _| |_  __ _| |_   _  _ ___ _  _   ___ ___ __|__ \
 | | | / / -_) \ V  V / ' \/ _` |  _| | || / _ \ || | (_-</ -_) -_)/_/
 |_|_|_\_\___|  \_/\_/|_||_\__,_|\__|  \_, \___/\_,_| /__/\___\___(_) 
                                       |__/                           
              __    _                             __
             / /_  (_)_______     ____ ___  ___  / /
            / __ \/ / ___/ _ \   / __ `__ \/ _ \/ / 
           / / / / / /  /  __/  / / / / / /  __/_/  
          /_/ /_/_/_/   \___/  /_/ /_/ /_/\___(_)   
                                          
       ------> linkedin.com/in/stephan-zwicknagl <------ """
        return printstr
    raise PreventUpdate()


if __name__ == '__main__':
    app.run(debug=True)