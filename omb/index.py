"""
Main app entry point and routing control
"""
print('index.py start')

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from omb.backend import dataset
from omb.app import app, server
from omb.apps import *

# make sure pycharm do not remove the import line...
type(server)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    print('Input pathname', pathname)
    pathname = '/' + pathname.split('/')[-1]
    print('Used pathname', pathname)

    if pathname == '/test':
        return test_app.layout
    if pathname == '/home':
        return home_app.layout
    if pathname == '/brain_table':
        return brain_table_app_layout
    if pathname == '/brain_region':
        return region_browser_app.layout
    if pathname == '/':
        return test_app.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
