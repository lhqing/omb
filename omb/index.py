"""
Main app entry point and routing control
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from omb.app import app
from omb.apps import *

app.config.suppress_callback_exceptions = True
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    # [State('url', 'search')]
)
def display_page(pathname, search):
    # print('url.pathname', pathname)
    # print('url.search', search)

    if pathname is None:
        # init callback url is None
        raise PreventUpdate

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
