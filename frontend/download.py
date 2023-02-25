from dash import html, dcc
from dash_iconify import DashIconify

download_content=[
            html.Div(
                html.Button(
                    id='download-button',
                    children=[
                        'Download your plots  ', 
                        DashIconify(icon="ic:baseline-download-for-offline", 
                                    height=20,
                                    style={'color': '#42bff5'})],
                    className='button', 
                    n_clicks=0)),
            dcc.Download(id="download-duration-plot"),
            dcc.Download(id="download-weekday-plot"),
            dcc.Download(id="download-calendar-plot"),
            dcc.Download(id="download-caller-plot"),
            dcc.Download(id="download-terminator-plot"),
        ]