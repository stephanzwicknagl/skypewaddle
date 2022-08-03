from turtle import onclick
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

colors = {
    "graphBackground": "#F5F5F5",
    "background": "#ffffff",
    "text": "#000000"
}

app.layout = html.Div([
    html.H1("Welcome to Skype Waddle"),
    html.Div(children="""
        This is a simple tool to visualize your personal Skype habits."""),
    html.Br(),
    html.Div(children=[
        """
        Just upload your Skype export file and see the results.
        """, "ⓘ"
    ],
             title="""
            Not sure how to export your Skype data?
            Just go to https://go.skype.com/export, login and submit a request for downloading your conversations
            """),
    dcc.Upload(id='my-upload',
               children=['Drag and Drop or ',
                         html.A('Select a File')],
               style={
                   'width': '50%',
                   'height': '60px',
                   'lineHeight': '60px',
                   'borderWidth': '1px',
                   'borderStyle': 'dashed',
                   'borderRadius': '5px',
                   'textAlign': 'center'
               },
               multiple=False),
    html.Br(),
    dcc.Graph(id="Mygraph"),
    html.Div(id='my-output'),
])


@app.callback(
    Output('Mygraph', 'figure'),
    [Input('my-upload', 'contents'),
     Input('my-upload', 'filename')])
def update_graph(contents, filename):
    x = []
    y = []
    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        df = df.set_index(df.columns[0])
        x = df['DATE']
        y = df['TMAX']
    fig = go.Figure(data=[go.Scatter(x=x, y=y, mode='lines+markers')],
                    layout=go.Layout(plot_bgcolor=colors["graphBackground"],
                                     paper_bgcolor=colors["graphBackground"]))
    return fig
# @app.callback(Output(component_id='my-output', component_property='children'),
#               Input(component_id='my-input', component_property='value'))
# def update_output_div(input_value):
#     return f'Output: {input_value}'


def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "json" in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return df

if __name__ == '__main__':
    app.run_server(debug=True)
