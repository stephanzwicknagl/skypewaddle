import base64
import io
import tarfile
from typing import IO, cast

import dash_bootstrap_components as dbc
import orjson
from dash import dcc
from plotly import graph_objects as go


def read_conversations_from_file(contents, filename):

    _, content_string = contents.split(',')
    decoded_data = base64.b64decode(content_string)

    if filename.endswith('.tar'):
        buffer = io.BytesIO(decoded_data)
        tar = tarfile.open(fileobj=buffer, mode="r")

        file = next(filter(lambda tar_element: tar_element.name == "messages.json", list(tar.getmembers())))
        decoded_data = cast(IO[bytes],tar.extractfile(file)).read()
    elif not filename.endswith('.json'):
        raise ValueError('File must be a .json or .tar file.')

    data = orjson.loads(decoded_data)
    return data['conversations'] if 'conversations' in data else None

def make_tab(figure: go.Figure):
    return dbc.Card(
        dbc.CardBody([
            dcc.Graph(figure=figure),
        ]),
        className="multi-tab",
    )