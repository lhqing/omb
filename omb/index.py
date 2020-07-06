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


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('url', 'search'),
     State('url', 'href')]
)
def display_page(pathname, search, total_url):
    # print('url.pathname', pathname)
    # print('url.search', search)
    app_layout = get_header()
    if pathname is None:
        # init callback url is None
        raise PreventUpdate
    elif pathname == '/home':
        pass
    elif pathname == '/brain_region':
        app_layout.children.append(region_browser_app.layout)
    elif pathname == '/cell_type':
        search_dict = search_to_dict(search)
        if search_dict is None:
            return '404'
        # validate key here:
        if 'ct' not in search_dict:
            return '404'
        layout = create_cell_type_browser_layout(cell_type_name=search_dict['ct'], total_url=total_url)
        if layout is None:
            return '404'
        else:
            app_layout.children.append(layout)
    elif pathname == '/test':
        app_layout.children.append(test_app.layout)
    elif pathname == '/gene':
        layout = create_gene_browser_layout()
        app_layout.children.append(layout)
    else:
        return '404'
    return app_layout


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
