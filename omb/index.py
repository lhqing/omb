"""
Main app entry point and routing control
"""

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from omb.App import *

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    print(pathname)
    if pathname == '/test':
        return test_app.layout
    if pathname == '/home':
        return home_app.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
