import base64
import tarfile
import io
import json

import dash_bootstrap_components as dbc
from dash import dcc
from plotly import graph_objects as go

def read_conversations_from_file(contents, filename):

    _, content_string = contents.split(',')
    decoded_data = base64.b64decode(content_string)

    data = {}
    if filename.endswith('.json'):
        data = json.load(io.BytesIO(decoded_data))
    elif filename.endswith('.tar'):
        buffer = io.BytesIO(decoded_data)
        tar = tarfile.open(fileobj=buffer, mode="r")

        file = next(filter(lambda tar_element: tar_element.name == "messages.json", list(tar.getmembers())))
        decoded_data = tar.extractfile(file)

        if decoded_data is not None:
            data = json.load(decoded_data)
        else:
            print("decoded_data is None")
    else:
        print("unknown file type")

    return data['conversations'] if 'conversations' in data else None

def make_tab(figure: go.Figure):
    return dbc.Card(
        dbc.CardBody([
            dcc.Graph(figure=figure),
        ]),
        className="multi-tab",
    )