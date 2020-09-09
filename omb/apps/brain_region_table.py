import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

from .default_values import *
from ..app import app

brain_region_df = dataset.brain_region_table.reset_index()

brain_table_app_layout = html.Div(children=[
    html.Div(children=[
        # basic numbers
        html.Div(
            [html.H6(id="brain_table_n_cells", children='N_CELLS'),
             html.P("Nuclei")],
            id="cellNumber",
            className="mini_container",
        ),
        html.Div(
            [html.H6(id="brain_table_n_regions", children='N_REGION'),
             html.P("Dissection Region")],
            id="regionNumber",
            className="mini_container",
        )],
        id='pretty_container two columns container-display'),
    dcc.Store(id='brain_region_table_selection_intermediate', data={'regions': []}),
    html.Div(children=[dash_table.DataTable(
        id='brain_region_table',
        style_cell={
            'whiteSpace': 'normal',
            # 'height': 'auto',
            'textAlign': 'left',
        },
        style_header={
            'fontWeight': 'bold',
            'height': '50px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        filter_action='native',
        sort_action="native",
        sort_mode="multi",
        row_selectable="multi",

        # this is important, must initialize this first so
        # update_brain_region_table_selected_rows can update this
        selected_rows=[],

        style_as_list_view=True,
        columns=[{"name": i, "id": i} for i in brain_region_df.columns],
        data=brain_region_df.to_dict('records'),
        page_size=18
    )], id='brain_region_table_div', className='ten columns pretty_container')
], className='row flex-display')


@app.callback(
    [Output('brain_region_table', 'selected_rows')],
    [Input('selected_dissection_region_store', "data")])
def update_brain_region_table(data):
    print('update_brain_region_table_selected_rows')
    print(data)
    selected_rows = [dataset.dissection_regions.index(r) for r in data['selected_region_names']]
    return [selected_rows]

