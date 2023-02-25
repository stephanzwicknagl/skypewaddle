import base64
import tarfile
import io

import dash_bootstrap_components as dbc
from dash import dcc
from plotly import graph_objects as go

def read_data_from_file(contents: str, filename: str):

    _, content_string = contents.split(',')
    decoded_data = base64.b64decode(content_string)

    data = io.BytesIO()
    if filename.endswith('.json'):
        data = io.BytesIO(decoded_data)
        # for item in ijson.items(io.BytesIO(decoded_data), 'conversations.item.id'):
        #     print(item)
        #     print(type(item))
    elif filename.endswith('.tar'):
        buffer = io.BytesIO(decoded_data)
        tar = tarfile.open(fileobj=buffer, mode="r")

        file = next(filter(lambda tar_element: tar_element.name == "messages.json", list(tar.getmembers())))
        data = tar.extractfile(file)
    else:
        print("unknown file type")

    return data

def make_tab(figure: go.Figure) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            dcc.Graph(figure=figure),
        ]),
        className="multi-tab",
    )