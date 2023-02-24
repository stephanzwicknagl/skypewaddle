from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify	



manual_text = """
- 🌐 Request and Download your Conversations from Skype (Microsoft). Follow the tutorial [here](https://support.skype.com/en/faq/FA34894/how-do-i-export-or-delete-my-skype-data).
    - 🕰 It may take a couple hours for Microsoft to serve your request. Just come back here once you have your file.
- ⬆️ Upload the file in the front page of Skype waddle and get your results.
- 😀 Enjoy and share!

- 🕐 Some of the results depend on the time zone of your device. Have your partner try it on their end to see their results.
"""

story_text = """
### The story behind

My partner and I were in a long distance relationship for 3 years. We used Skype to talk to each other every day. 

During the pandemic, we would talk for hours and hours. 

We started to wonder how much we actually skyped. That's why I created this tool.

Here, you can analyze 

"""

# type: ignore 
info_content = [
    html.Div(id="info-open", n_clicks=0, children=[
                DashIconify(icon="material-symbols:info",
                height=20,
                className="info",
                style={"color": "#00aff0"})
            ]),
    dbc.Modal(id="info-modal", is_open=False, children=[
            dbc.ModalHeader(dbc.ModalTitle("How To Use Skype Waddle")),
                dbc.ModalBody(children=[
                    dcc.Markdown([manual_text, story_text],
                        link_target="_blank",
                        style={"overflow": "scroll"})
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="info-close", className="ms-auto", n_clicks=0
                    ))
                ]),
]