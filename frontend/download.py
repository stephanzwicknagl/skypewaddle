import dash_bootstrap_components as dbc
from dash import dcc, html
from dash_iconify import DashIconify

download_content=[
            html.Div(
                dbc.Button(
                    id='download-button',
                    children=[
                        'Download your plots  ', 
                        DashIconify(icon="ic:baseline-download-for-offline", 
                                    height=20,
                                    style={'color': '#f8f8ff'})],
                    className='button', 
                    n_clicks=0)),
            dcc.Download(id="download-duration-plot"),
            dcc.Download(id="download-weekday-plot"),
            dcc.Download(id="download-calendar-plot"),
            dcc.Download(id="download-caller-plot"),
            dcc.Download(id="download-terminator-plot"),
        ]