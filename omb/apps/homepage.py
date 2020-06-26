import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output

from dash.exceptions import PreventUpdate
from omb.app import app
from .default_values import *

CELL_TYPE_LEVELS = ['CellClass', 'MajorType', 'SubType']
REGION_LEVELS = ['MajorRegion', 'SubRegion', 'Region']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', ]

home_app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

home_app.layout = html.Div(children=[
    # first column 2/12
    html.Div(children=[
        html.Div(
            [html.H6(id="n_cells", children=N_CELLS), html.P("Nuclei")],
            id="cellNumber",
            className="mini_container",
        ),
        html.Div(
            [html.H6(id="n_region", children=N_REGION), html.P("Brain Region")],
            id="regionNumber",
            className="mini_container",
        ),
        html.Div(
            [html.H6(id="n_major_type", children=N_MAJOR_TYPE), html.P("Major Types")],
            id="majorTypeNumber",
            className="mini_container",
        ),
        html.Div(
            [html.H6(id="n_subtype", children=N_SUBTYPE), html.P("Subtypes")],
            id="subtypeNumber",
            className="mini_container",
        ),
        html.Div([html.P("Sunburst Type"),
                  dcc.Dropdown(
                      options=[
                          {'label': 'Brain Region', 'value': 'region'},
                          {'label': 'Cell Type', 'value': 'cell_type'}
                      ],
                      value='cell_type',
                      id="sunburst_type",
                  )],
                 id='control_graph2',
                 className="mini_container",
                 ),
        html.Div(
            # control panel
            [html.P("Coordinates"),
             dcc.Dropdown(
                 options=[
                     {'label': 'tSNE', 'value': 'L1TSNE'},
                     {'label': 'UMAP', 'value': 'L1UMAP'}
                 ],
                 value='L1UMAP',
                 id="coord_selection",
             ),
             html.P("Color"),
             dcc.Dropdown(
                 options=[
                     {'label': 'Dissection Region', 'value': 'Region'},
                     {'label': 'Sub-Region', 'value': 'SubRegion'},
                     {'label': 'Major Region', 'value': 'MajorRegion'},
                     {'label': 'Cell Class', 'value': 'CellClass'},
                     {'label': 'Major Type', 'value': 'MajorType'},
                     {'label': 'Subtype', 'value': 'SubType'},
                 ],
                 value='Region',
                 id="color_selection",
             ),
             html.P("Marker Size"),
             dcc.Slider(
                 min=1,
                 max=4,
                 step=0.3,
                 value=1.8,
                 id='marker_size_slider')],
            id='control_graph2',
            className="mini_container",
        ),
    ], className='two columns pretty_container control_panel'),

    # Second column 5/12
    html.Div(children=[
        dcc.Graph(
            id='homepage_graph1'
        )
    ], id='homepage_graph1_div', className='five columns pretty_container data_panel'),

    # Third column 5/12
    html.Div(children=[
        dcc.Graph(
            id='homepage_graph2'
        )
    ], id='homepage_graph2_div', className='five columns pretty_container data_panel'),
])


@app.callback(
    Output('homepage_graph1', 'figure'),
    [Input('sunburst_type', 'value')]
)
def update_graph_1(sunburst_type):
    if sunburst_type == 'cell_type':
        levels = CELL_TYPE_LEVELS
    elif sunburst_type == 'region':
        levels = REGION_LEVELS
    else:
        levels = CELL_TYPE_LEVELS

    data = dataset.get_variables(levels)
    if 'SubType' in levels:
        data = data[data['SubType'].apply(lambda i: 'Outlier' not in i)]

    # prepare count table
    count_df = data.groupby(levels).apply(lambda i: i.shape[0]).reset_index()
    count_df.columns = levels + ['Cell Number']

    # prepare total palette
    total_palette = {}
    for level in levels:
        total_palette.update(dataset.get_palette(level))

    # prepare sunburst
    labels = []
    parents = []
    values = []
    colors = []
    for level, parent_level in zip(levels[::-1], levels[1::-1] + [None]):
        this_level_sum = count_df.groupby(level)['Cell Number'].sum().to_dict()
        this_level_sum = {k: v for k, v in this_level_sum.items() if v != 0}
        if parent_level is not None:
            this_parent_dict = count_df.set_index(level)[parent_level].to_dict()
        else:
            this_parent_dict = {label: '' for label in count_df[level].unique()}
        for label in this_level_sum.keys():
            labels.append(label)
            parents.append(this_parent_dict[label])
            values.append(this_level_sum[label])
            try:
                colors.append(total_palette[label])
            except KeyError:
                colors.append('#D3D3D3')

    # Here is a sunburst example
    # fig = go.Figure(go.Sunburst(
    #     labels=["Eve", "Cain", "Seth", "Enos", "Noam", "Abel", "Awan", "Enoch", "Azura"],
    #     parents=["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve"],
    #     values=[65, 14, 12, 10, 2, 6, 6, 4, 4],
    #     branchvalues="total",
    # ))
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker={'colors': colors},  # only in this way, I can precisely control the color
        branchvalues="total",
    ))
    # Update layout for tight margin
    # See https://plotly.com/python/creating-and-updating-figures/
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    return fig


@app.callback(
    Output('homepage_graph2', 'figure'),
    [Input('coord_selection', 'value'),
     Input('color_selection', 'value'),
     Input('marker_size_slider', 'value')])
def update_graph_2_scatter_plot(coord_base, color_name, marker_size):
    if coord_base is None or color_name is None:
        raise PreventUpdate
    hue_palette = dataset.get_palette(color_name)
    plot_df = dataset.get_coords(coord_base)

    _hover_cols = ['RegionName', 'SubType']
    if color_name not in _hover_cols:
        _hover_cols.append(color_name)
    for col_name in _hover_cols:
        plot_df[col_name] = dataset.get_variables(col_name).astype(str)

    # make figure
    fig = px.scatter(plot_df,
                     x="x",
                     y="y",
                     color=color_name,
                     color_discrete_map=hue_palette,
                     hover_name=color_name,
                     hover_data=_hover_cols)
    fig.update_layout(showlegend=False,
                      legend={'itemsizing': 'constant'},
                      xaxis=go.layout.XAxis(title='', showticklabels=False),
                      yaxis=go.layout.YAxis(title='', showticklabels=False),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')

    # update marker size and hover template
    fig.update_traces(mode='markers', marker_size=marker_size,
                      hovertemplate='<b>%{hovertext}</b><br>'
                                    '<b>Dissection Region: </b>%{customdata[0]}<br>'
                                    '<b>SubType: </b>%{customdata[1]}')
    return fig


@app.callback(
    Output('homepage_graph2', 'selectedData'),
    [Input('homepage_graph1', 'clickData'),
     Input('sunburst_type', 'value')]
)
def update_sunburst_click(click_data, sunburst_type):
    if click_data is None:
        raise PreventUpdate

    click_label = click_data['points'][0]['label']
    try:
        level = click_data['points'][0]['currentPath'].count('/') - 1  # this number corresponding to the level number
    except KeyError:
        # there is a 'currentPath' key error, it happens when clicking the same label twice, so no update
        print(click_data)
        raise PreventUpdate
    if sunburst_type == 'cell_type':
        col_name = CELL_TYPE_LEVELS[level]
    elif sunburst_type == 'region':
        col_name = REGION_LEVELS[level]
    else:
        col_name = CELL_TYPE_LEVELS[level]

    _col = dataset.get_variables(col_name)
    # this is the corresponding cell ids from sunburst click
    cell_ids = _col[_col == click_label].index
    print(len(cell_ids))
    return {'points': cell_ids}


# @app.callback(
#     Output('n_cells', 'children'),
#     Output('n_cells', 'children'),
#     [Input('homepage_graph2', 'selectedData')]
# )
# def update_scatter_click(selected_data):
#     if not selected_data:
#         raise PreventUpdate
#     print(len(selected_data['points']))
#     print(selected_data.keys())
#     return len(selected_data['points'])


if __name__ == '__main__':
    home_app.run_server(debug=True, port=1234)
