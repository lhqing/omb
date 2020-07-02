"""
Main app entry point and routing control
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from omb.app import app
from omb.apps import *

app.config.suppress_callback_exceptions = True
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


def search_to_dict(search):
    if search is None:
        return None
    kv_pairs = search[1:].split(';')  # remove ?
    search_dict = {}
    for kv in kv_pairs:
        try:
            k, v = kv.split('=')
            search_dict[k] = v
        except IndexError:
            return None
    return search_dict


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('url', 'search')]
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
    if pathname == '/cell_type':
        search_dict = search_to_dict(search)
        if search_dict is None:
            return '404'
        # validate key here:
        if 'ct' not in search_dict:
            return '404'
        return create_cell_type_browser_layout(cell_type_name=search_dict['ct'])
    if pathname == '/':
        return test_app.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
