"""
Main app entry point and routing control
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from omb.app import app, server, APP_ROOT_NAME
from omb.apps import *


def search_to_dict(search):
    if search is None:
        return None
    kv_pairs = search[1:].split(';')  # remove ?
    search_dict = {}
    for kv in kv_pairs:
        try:
            k, v = kv.split('=')
            search_dict[k] = v
        except (IndexError, ValueError):
            return None
    return search_dict


def get_header():
    return html.Div(
        children=[
            html.Div(children=[
                html.Img(
                    src='https://github.com/lhqing/omb/raw/master/omb/assets/dissection_region_img/navbar_icon.gif',
                    className='nav-icon'),
                dcc.Link(
                    "Home",
                    href="/home",
                    className="tab first",
                ),
                dcc.Link(
                    "Gene Browser",
                    href="/gene?gene=Cux2",
                    className="tab",
                ),
                dcc.Link(
                    "Brain Region Browser",
                    href="/brain_region",
                    className="tab",
                ),
                dcc.Link(
                    "Cell Type Browser",
                    href="/cell_type?ct=Exc",
                    className="tab",
                )
            ],
                className="row all-tabs")
        ]
    )


# make sure pycharm do not remove the import line...
# because server need to be imported by wsgi.py from index.py
# all orders matters here
type(server)

# this is only based on my own server
# server deploy setting, change APP_NAME based on the routing config in apache
app.config.suppress_callback_exceptions = True
app.config.update({
    # remove the default of '/'
    'routes_pathname_prefix': f'/{APP_ROOT_NAME}/',

    # remove the default of '/'
    'requests_pathname_prefix': f'/{APP_ROOT_NAME}/'
})
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    get_header(),  # nav bar
    html.Div(id='page-content', className='content')
])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('url', 'search'),
     State('url', 'href')]
)
def display_page(pathname, search, total_url):
    # print('url.pathname', pathname)
    # print('url.search', search)
    app_layout = []
    search_dict = search_to_dict(search)

    if pathname is None:
        # init callback url is None
        raise PreventUpdate
    elif (pathname == f'/{APP_ROOT_NAME}/home') or (pathname == f'/{APP_ROOT_NAME}/'):
        app_layout.append(home_layout)
    elif pathname == f'/{APP_ROOT_NAME}/brain_region':
        app_layout.append(region_browser_app.layout)
    elif pathname == f'/{APP_ROOT_NAME}/cell_type':
        if search_dict is None:
            return '404'
        # validate key here:
        if 'ct' not in search_dict:
            return '404'
        layout = create_cell_type_browser_layout(cell_type_name=search_dict['ct'], total_url=total_url)
        if layout is None:
            return '404'
        else:
            app_layout.append(layout)
    elif pathname == f'/{APP_ROOT_NAME}/gene':
        if search_dict is None:
            return '404'
        # validate key here:
        if 'gene' not in search_dict:
            return '404'
        layout = create_gene_browser_layout(gene=search_dict['gene'])
        if layout is None:
            return '404'
        app_layout.append(layout)
    elif pathname == f'/{APP_ROOT_NAME}/test':
        app_layout.append(test_app.layout)
    else:
        return '404'
    return app_layout
