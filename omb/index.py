"""
Main app entry point and routing control
"""
print('index.py start')

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from omb.app import app, server
from omb.apps import *

# make sure pycharm do not remove the import line...
type(server)

# this is only based on my own server
# server deploy setting, change APP_NAME based on the routing config in apache
APP_NAME = 'omb'

app.config.suppress_callback_exceptions = True
app.config.update({
    # remove the default of '/'
    'routes_pathname_prefix': f'/{APP_NAME}/',

    # remove the default of '/'
    'requests_pathname_prefix': f'/{APP_NAME}/'
})

print(app.config)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        raise PreventUpdate
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
