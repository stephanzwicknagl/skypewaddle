# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from backend import extraction as extraction
from dash.dependencies import Input, Output, State

app = Dash(__name__, title="skype waddle", update_title=None)

app.layout = html.Div(children=[
    html.H1(children='Skype Waddle'),

    html.Div(children='''
        Analyze your Skype habits...
        Upload your data to get started 🚀
    '''),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        className="upload",
        style={

        }
    ),
    html.Div(id='select-participant')
])


@app.callback(Output('select-participant', 'children'),
              Input('upload-data', 'contents'))
def update_output(contents):
    if contents is not None:
        content_type, content_string = contents.split(',')
        _, participants = extraction.extract_conversations(content_string)
        print("lalala")
        print(participants)
        children = [
            #return a dropdown with all the participants
            dcc.Dropdown(
                id='participants',
                options=[{'label': i, 'value': i} for i in participants])
            ]
        return children


if __name__ == '__main__':
    app.run_server(debug=True)
