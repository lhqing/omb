"""
Main app entry point and routing control
"""
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from omb.app import app, server, APP_ROOT_NAME
from omb.apps import *


def search_to_dict(search):
    if search is None:
        return None
    kv_pairs = search[1:].split(';')  # remove "?"
    search_dict = {}
    for kv in kv_pairs:
        try:
            k, v = kv.split('=')
            search_dict[k] = v
        except (IndexError, ValueError):
            return None
    return search_dict


def get_header():
    logo_img_url = 'http://neomorph.salk.edu/omb_static/dissection_region_img/navbar_icon.gif'
    nav = dbc.Row(
        [
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink('Home', href=f"/{APP_ROOT_NAME}home")),
                    dbc.NavItem(dbc.NavLink('Gene', href=f"/{APP_ROOT_NAME}gene?gene=Cux2")),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem('Region Table', href=f"/{APP_ROOT_NAME}br_table"),
                            dbc.DropdownMenuItem('Region Viewer', href=f"/{APP_ROOT_NAME}brain_region?br=MOp")
                        ],
                        label='Brain Region',
                        nav=True,
                        in_navbar=True
                    ),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem('Cell Type Table', href=f'/{APP_ROOT_NAME}ct_table'),
                            dbc.DropdownMenuItem('Cell Type Viewer', href=f'/{APP_ROOT_NAME}cell_type?ct=Exc')
                        ],
                        label='Cell Type',
                        nav=True,
                        in_navbar=True
                    ),
                    dbc.NavItem(dbc.NavLink('Paired Scatter', href=f"/{APP_ROOT_NAME}scatter")),
                ],
                className='mr-5',
                navbar=True,
                style={'font-size': '1.4em'}
            )
        ],
        className="ml-2 flex-nowrap mt-3 mt-md-0",
        align="center",
    )

    navbar = dbc.Navbar(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=logo_img_url, height='50px'))
                    ],
                    align='left',
                    no_gutters=True
                ),
                href=f"/{APP_ROOT_NAME}",
                className='mx-3'
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(nav, id="navbar-collapse", navbar=True),
        ],
        color='light',
        className='fixed-top mb-2 p-2'
    )
    return navbar


# make sure pycharm do not remove the import line...
# because server need to be imported by wsgi.py from index.py
# all orders matters here
type(server)

app.config.suppress_callback_exceptions = True
app.config.update(
    {
        'routes_pathname_prefix': f'/{APP_ROOT_NAME}',
        'requests_pathname_prefix': f'/{APP_ROOT_NAME}'
    }
)

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        get_header(),  # nav bar
        html.Div(
            id='page-content',
            # Global style of all APPs
            className='page-content'
        )
    ]
)


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('url', 'search'),
     State('url', 'href')]
)
def display_page(pathname, search, total_url):
    app_layout = []
    search_dict = search_to_dict(search)

    if pathname is None:
        # init callback url is None
        raise PreventUpdate
    elif (pathname == f'/{APP_ROOT_NAME}home') or (pathname == f'/{APP_ROOT_NAME}'):
        layout = home_layout
    elif pathname == f'/{APP_ROOT_NAME}brain_region':
        if search_dict is None:
            return '404'
        # validate key here:
        if 'br' not in search_dict:
            return '404'
        layout = create_brain_region_browser_layout(region_name=search_dict['br'])
    elif pathname == f'/{APP_ROOT_NAME}br_table':
        layout = create_brain_table_layout()
    elif pathname == f'/{APP_ROOT_NAME}cell_type':
        if search_dict is None:
            return '404'
        # validate key here:
        if 'ct' not in search_dict:
            return '404'
        layout = create_cell_type_browser_layout(cell_type_name=search_dict['ct'], total_url=total_url)
    elif pathname == f'/{APP_ROOT_NAME}ct_table':
        layout = create_cell_type_table_layout()
    elif pathname == f'/{APP_ROOT_NAME}gene':
        if search_dict is None:
            return '404'
        # validate key here:
        if 'gene' not in search_dict:
            return '404'
        layout = create_gene_browser_layout(gene=search_dict['gene'])
    elif pathname == f'/{APP_ROOT_NAME}scatter':
        layout = create_paired_scatter_layout(**paired_scatter_api(search_dict))
    elif pathname == f'/{APP_ROOT_NAME}ct_dmr':
        layout = create_cell_type_dmr_layout()
    else:
        return '404'

    # final validate, if any parameter does not found, layout is None
    if layout is None:
        return '404'
    else:
        app_layout.append(layout)
    return app_layout


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
