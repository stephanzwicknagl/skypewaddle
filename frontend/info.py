from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify	



manual_text = """
- 🌐 Request and Download a copy of your Skype chat history from Microsoft. Follow the tutorial [here](https://support.skype.com/en/faq/FA34894/how-do-i-export-or-delete-my-skype-data). (Download your Conversations only)
    - 🕰 It may take a couple hours for Microsoft to serve your request. Just come back here once you have your file.
- ⬆️ Upload the `.tar` file in the front page of _Skype Waddle_ and get your results.
- 😀 Enjoy and share!

- 🕐 Some of the results depend on the time zone of your device. If you live in different time zonees, have your partner try it on their end to see their results.

Want to use some sample data first?
"""

story_text = """
### The story behind _Skype Waddle_

My partner and I were in a long distance relationship for 3 years. We used Skype to talk to each other every day. 

During the pandemic, we would talk for hours and hours. 

We started to wonder how much we actually skyped. That's why I created this tool.

Here, you can analyze how much you video chat with your partner, friends or family. Find out how many hours, how many calls, the duration of your calls over time and more.
"""

disclaimer_text = """
### Disclaimer

Your data is processed on the servers of Heroku and is not stored anywhere else. It is only used to generate the graphs and deleted when you end your session.

This tool is not affiliated with Microsoft or Skype. It is not endorsed by Microsoft or Skype. It is not sponsored by Microsoft or Skype.

"""

info_content = [
    # type: ignore 
    html.Div(id="info-open", n_clicks=0, children=[
                DashIconify(icon="material-symbols:info",
                height=25,
                className="info",
                style={"color": "#00aff0"})
            ]),
    dbc.Modal(id="info-modal", is_open=False, children=[
            dbc.ModalHeader(dbc.ModalTitle(["How To Use ", html.Em("Skype Waddle")])),
                dbc.ModalBody(children=[
                    dcc.Markdown([manual_text],
                        link_target="_blank"),
                    dbc.Button("Download sample data", id="sample-data-button", n_clicks=0, className="button", style={"marginBottom": "1rem"}),
                    dcc.Download(id="download-sample-data"),
                    dcc.Markdown([story_text, disclaimer_text],
                        link_target="_blank"),
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="info-close", className="ms-auto", n_clicks=0
                    ))
                ]),
]