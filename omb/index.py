"""
Main app entry point and routing control
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from omb.app import app
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


app.config.suppress_callback_exceptions = True
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
    elif (pathname == '/home') or (pathname == '/'):
        app_layout.append(home_layout)
    elif pathname == '/brain_region':
        app_layout.append(region_browser_app.layout)
    elif pathname == '/cell_type':
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
    elif pathname == '/gene':
        if search_dict is None:
            return '404'
        # validate key here:
        if 'gene' not in search_dict:
            return '404'
        layout = create_gene_browser_layout(gene=search_dict['gene'])
        if layout is None:
            return '404'
        app_layout.append(layout)
    elif pathname == '/test':
        app_layout.append(test_app.layout)
    else:
        return '404'
    return app_layout


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
