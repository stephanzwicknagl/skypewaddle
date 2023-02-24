from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify	

warn_text = """
There was an error processing your data.
There are too many invalid calls, which cause the results to be inaccurate.
Try again with a different file.
"""

warn_content = dbc.Modal(id="warn-modal", is_open=False, children=[
            dbc.ModalHeader(dbc.ModalTitle("Error")),
                dbc.ModalBody(children=[
                    dcc.Markdown([warn_text],
                    style={"overflow": "scroll"})
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Dismiss", id="warn-close", className="ms-auto", n_clicks=0
                    ))
                ])


