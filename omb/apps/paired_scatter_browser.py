import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from .cell_type_browser import TOTAL_GENE_OPTIONS
from .default_values import *
from .utilities import n_cell_to_marker_size
from ..app import app


def paired_scatter_api(search_dict):
    if search_dict is None:
        search_dict = {}
    # scatter plot api
    parameters = {
        'coords': search_dict.get('coords', 'L1UMAP'),
        'downsample': search_dict.get('sample', 10000),
        'brain_regions': search_dict.get('br', 'ALL REGIONS'),
        'cell_types': search_dict.get('ct', 'ALL CELLS'),
        'cell_meta_hue': search_dict.get('meta', 'MajorType'),
        'gene': search_dict.get('gene', 'Cux2'),
        'mc_type': search_dict.get('mc', 'CHN'),
        'cnorm': search_dict.get('cnorm', '0.5,1.5')
    }
    parameters['brain_regions'] = parameters['brain_regions'].replace('%20', ' ').split(',')
    parameters['cell_types'] = parameters['cell_types'].replace('%20', ' ').split(',')
    try:
        parameters['cnorm'] = list(map(float, parameters['cnorm'].split(',')))
        if len(parameters['cnorm']) != 2:
            raise ValueError
    except ValueError:
        parameters['cnorm'] = (0.5, 1.5)
    return parameters


def _get_active_and_background_data(coords, downsample,
                                    cell_types, brain_regions,
                                    cell_meta_hue, gene_int,
                                    gene_mc_type):
    plot_data = dataset.get_coords(coords)
    gene_name = dataset.gene_meta_table.loc[gene_int, 'gene_name']

    # get unique selected subtypes and dissection regions
    selected_subtypes = []
    for ct in cell_types:
        if ct == 'ALL CELLS':
            selected_subtypes = dataset.cell_type_table[
                dataset.cell_type_table['Cluster Level'] ==
                'SubType'].index.tolist()
            break
        else:
            selected_subtypes += dataset.cluster_name_to_subtype(ct)
    selected_subtypes = set(selected_subtypes)

    selected_dissection_regions = []
    for br in brain_regions:
        selected_dissection_regions += dataset.region_label_to_dissection_region_dict[
            br]
    selected_dissection_regions = set(selected_dissection_regions)

    # judge active cells
    plot_data['SubType'] = dataset.get_variables('SubType').astype(str)
    plot_data['RegionName'] = dataset.get_variables('RegionName').astype(str)
    plot_data['active'] = (plot_data['SubType'].isin(selected_subtypes)) & (
        plot_data['RegionName'].isin(selected_dissection_regions))

    # add cell meta and gene color data
    if cell_meta_hue not in plot_data.columns:
        plot_data[cell_meta_hue] = dataset.get_variables(cell_meta_hue)
        if cell_meta_hue in CATEGORICAL_VAR:
            plot_data[cell_meta_hue] = plot_data[cell_meta_hue].astype(str)
    plot_data[gene_name] = dataset.get_gene_rate(gene_int, mc_type=gene_mc_type)

    # split active and background
    active_data = plot_data[plot_data['active']].copy()
    background_data = plot_data[~plot_data['active']].copy()
    if active_data.shape[0] > downsample:
        active_data = active_data.sample(downsample, random_state=0)
    if background_data.shape[0] > downsample:
        background_data = background_data.sample(downsample, random_state=0)
    return active_data, background_data


def create_paired_scatter_layout(coords='L1UMAP', downsample=10000,
                                 brain_regions=None, cell_types=None,
                                 cell_meta_hue='MajorType', gene=15397,
                                 mc_type='CHN', cnorm=(0.5, 1.5)):
    try:
        gene_int = int(gene)
    except ValueError:
        gene_int = dataset.gene_name_to_int[gene]
    possible_cell_types = ['ALL CELLS'] + dataset.cell_type_table.index.tolist()

    # Forms
    layout_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Coordinates', html_for='coords-dropdown'),
                    dcc.Dropdown(
                        id='coords-dropdown',
                        options=[{'label': name, 'value': name}
                                 for name in dataset.coord_names],
                        value=coords,
                        clearable=False),
                    dbc.FormText('Coordinates of both scatter plots.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Down Sample Cells', html_for='down-sample-dropdown'),
                    dcc.Dropdown(
                        id='down-sample-dropdown',
                        options=[{'label': '10000 (Fast)', 'value': 10000},
                                 {'label': '50000 (Slow)', 'value': 50000},
                                 {'label': 'ALL (Very Slow)', 'value': 9999999}],
                        value=downsample,
                        clearable=False
                    ),
                    dbc.FormText('Number of cells plotted on each scatter plot.')
                ]
            )
        ]
    )

    active_cells_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Select by Brain Regions', html_for='brain-region-select-dropdown'),
                    dcc.Dropdown(
                        id='brain-region-select-dropdown',
                        options=[{'label': region, 'value': region}
                                 for region in dataset.region_label_to_dissection_region_dict.keys()],
                        multi=True,
                        value=brain_regions,
                        placeholder='ALL REGIONS by default'
                    ),
                    dbc.FormText('Only color cells from these brain regions.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Select by Cell Types', html_for='cell-type-select-dropdown'),
                    dcc.Dropdown(
                        id='cell-type-select-dropdown',
                        options=[{'label': ct, 'value': ct}
                                 for ct in possible_cell_types],
                        multi=True,
                        value=cell_types,
                        placeholder='ALL CELLS by default'
                    ),
                    dbc.FormText('Only color cells from these cell types.')
                ]
            )
        ]
    )

    colors_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Cell Metadata', html_for='cell-meta-dropdown'),
                    dcc.Dropdown(
                        id='cell-meta-dropdown',
                        options=[{'label': VAR_NAME_MAP[name], 'value': name}
                                 for name in CONTINUOUS_VAR + CATEGORICAL_VAR],
                        value=cell_meta_hue,
                        clearable=False
                    ),
                    dbc.FormText('Color of the left scatter plot.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Gene', html_for='scatter-gene-dropdown'),
                    dcc.Dropdown(id='scatter-gene-dropdown',
                                 value=gene_int,
                                 placeholder='Input a gene name, e.g. Cux2'),
                    dbc.FormText('Gene of the right scatter plot.')
                ]
            )
        ]
    )

    gene_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Gene Body mC Type', html_for='scatter-mc-type-dropdown'),
                    dcc.Dropdown(id='scatter-mc-type-dropdown',
                                 options=[{'label': 'Norm. mCH / CH', 'value': 'CHN'},
                                          {'label': 'Norm. mCG / CG', 'value': 'CGN'}],
                                 value=mc_type,
                                 clearable=False),
                    dbc.FormText('Color per cell normalized mCH or mCG fraction of the gene body.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Gene Color Scale', html_for='gene-color-range-slider'),
                    dcc.RangeSlider(
                        id='gene-color-range-slider',
                        min=0,
                        max=3,
                        step=0.1,
                        marks={0: '0', 0.5: '0.5', 1: '1',
                               1.5: '1.5', 2: '2', 2.5: '2.5',
                               3: '3'},
                        value=cnorm
                    ),
                    dbc.FormText('Color scale of the right scatter plot.')
                ]
            )
        ]
    )

    first_row = dbc.Row(
        [
            # submission button
            dbc.Col(
                [
                    html.H4('Scatter Control', className='card-title text-center'),
                    dbc.Button(
                        'CLICK TO UPDATE',
                        id='update-button',
                        n_clicks=0,
                        color='success'
                    )
                ],
                width=12, xl=1,
                className='h-100 p-3 m-auto'
            ),
            # control
            dbc.Col(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader('Scatter Layout'),
                                            dbc.CardBody(
                                                [
                                                    layout_form
                                                ]
                                            )
                                        ],
                                        className='h-100'
                                    )
                                ],
                                width=12, md=6, xl=3
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader('Active Cells'),
                                            dbc.CardBody(
                                                [
                                                    active_cells_form
                                                ]
                                            )
                                        ],
                                        className='h-100'
                                    ),
                                ],
                                width=12, md=6, xl=3
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader('Color By'),
                                            dbc.CardBody(
                                                [
                                                    colors_form
                                                ]
                                            )
                                        ],
                                        className='h-100'
                                    ),
                                ],
                                width=12, md=6, xl=3
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader('Gene Detail'),
                                            dbc.CardBody(
                                                [
                                                    gene_form
                                                ]
                                            )
                                        ],
                                        className='h-100'
                                    )
                                ],
                                width=12, md=6, xl=3
                            ),
                        ]
                    )
                ],
                width=12, xl=11
            )
        ]
    )

    second_row = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Cell Metadata Scatter'),
                            dbc.Container(
                                [
                                    dcc.Graph(id='cell-meta-graph',
                                              style={"height": "80vh", "width": "auto"})
                                ],
                                className='pt-3'
                            )
                        ]
                    )
                ],
                width=12, xl=6
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Gene Scatter'),
                            dbc.Container(
                                [
                                    dcc.Graph(id='gene-graph',
                                              style={"height": "80vh", "width": "auto"})
                                ],
                                className='pt-3'
                            )
                        ]
                    )
                ],
                width=12, xl=6
            )
        ],
        className='my-4'
    )
    layout = html.Div(children=[
        # first row is controls
        first_row,

        # second row is two scatter graph, left is cell metadata, right is gene
        dcc.Loading(
            second_row
        )
    ])
    return layout


@app.callback(
    Output('scatter-gene-dropdown', 'options'),
    [Input('scatter-gene-dropdown', 'search_value')]
)
def update_gene_options(search_value):
    if not search_value:
        raise PreventUpdate

    this_options = [o for o in TOTAL_GENE_OPTIONS if search_value in o["label"]]
    if len(this_options) > 100:
        return [{'label': 'Keep typing...', 'value': 'NOT A GENE', 'disabled': True}]
    else:
        return this_options


@app.callback(
    [Output('cell-meta-graph', 'figure'),
     Output('gene-graph', 'figure')],
    [Input('update-button', 'n_clicks')],
    [State('coords-dropdown', 'value'),
     State('down-sample-dropdown', 'value'),
     State('cell-type-select-dropdown', 'value'),
     State('brain-region-select-dropdown', 'value'),
     State('cell-meta-dropdown', 'value'),
     State('scatter-gene-dropdown', 'value'),
     State('scatter-mc-type-dropdown', 'value'),
     State('gene-color-range-slider', 'value')]
)
def update_both_scatters(_n_clicks, coords, downsample,
                         cell_types, brain_regions,
                         cell_meta_hue, gene_int,
                         gene_mc_type, cnorm):
    if gene_int is None:
        gene_int = dataset.gene_name_to_int['Cux2']
    gene_name = dataset.gene_meta_table.loc[gene_int, 'gene_name']

    # print(_n_clicks)
    active_data, background_data = _get_active_and_background_data(
        coords=coords, downsample=downsample,
        cell_types=cell_types, brain_regions=brain_regions,
        cell_meta_hue=cell_meta_hue, gene_int=gene_int,
        gene_mc_type=gene_mc_type)

    # cell meta plot
    if cell_meta_hue in CONTINUOUS_VAR:
        hue_norm = CONTINUOUS_VAR_NORMS.get(cell_meta_hue, None)
        active_data[cell_meta_hue] = active_data[cell_meta_hue].astype(float)
        fig_cell_meta = px.scatter(data_frame=active_data,
                                   x='x',
                                   y='y',
                                   color=cell_meta_hue,
                                   range_color=hue_norm,
                                   color_continuous_scale='Viridis',
                                   hover_name='SubType',
                                   hover_data=[cell_meta_hue])
        # update marker size and hover template
        fig_cell_meta.update_traces(mode='markers',
                                    marker_size=n_cell_to_marker_size(
                                        active_data.shape[0]),
                                    hovertemplate='<b>%{hovertext}</b><br>'
                                                  f'<b>{cell_meta_hue}: </b>%{{customdata[0]:.3f}}')
    else:
        fig_cell_meta = px.scatter(
            active_data,
            x="x",
            y="y",
            color=cell_meta_hue,
            color_discrete_map=dataset.get_palette(cell_meta_hue),
            hover_name='SubType',
            hover_data=[cell_meta_hue])
        # update marker size and hover template
        fig_cell_meta.update_traces(mode='markers',
                                    marker_size=n_cell_to_marker_size(
                                        active_data.shape[0]),
                                    hovertemplate='<b>%{hovertext}</b><br>'
                                                  f'<b>{cell_meta_hue}: </b>%{{customdata[0]}}')

    fig_cell_meta.update_layout(showlegend=False,
                                margin=dict(t=15, l=0, r=0, b=15),
                                xaxis=go.layout.XAxis(title='',
                                                      showticklabels=False,
                                                      showgrid=False,
                                                      zeroline=False),
                                yaxis=go.layout.YAxis(title='',
                                                      showticklabels=False,
                                                      showgrid=False,
                                                      zeroline=False),
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)')
    # unselected_plot_df is gray background, no hover
    if background_data.shape[0] > 10:
        fig_cell_meta.add_trace(
            go.Scattergl(
                x=background_data['x'],
                y=background_data['y'],
                mode='markers',
                name='Others',
                marker_size=n_cell_to_marker_size(background_data.shape[0]) - 1,
                marker_color='rgba(200, 200, 200, .5)',
                hoverinfo='skip')
        )
    # reorder data to put the background trace in first (bottom)
    fig_cell_meta.data = fig_cell_meta.data[::-1]

    # gene figure
    fig_gene = px.scatter(data_frame=active_data,
                          x='x',
                          y='y',
                          color=gene_name,
                          range_color=cnorm,
                          color_continuous_scale='Viridis',
                          hover_name='SubType',
                          hover_data=[gene_name])
    # update marker size and hover template
    fig_gene.update_traces(mode='markers',
                           marker_size=n_cell_to_marker_size(active_data.shape[0]),
                           hovertemplate='<b>%{hovertext}</b><br>'
                                         f'<b>{gene_name} m{gene_mc_type[:-1]}: </b>%{{customdata[0]:.3f}}')
    fig_gene.update_layout(showlegend=False,
                           margin=dict(t=15, l=0, r=0, b=15),
                           xaxis=go.layout.XAxis(title='',
                                                 showticklabels=False,
                                                 showgrid=False,
                                                 zeroline=False),
                           yaxis=go.layout.YAxis(title='',
                                                 showticklabels=False,
                                                 showgrid=False,
                                                 zeroline=False),
                           plot_bgcolor='rgba(0,0,0,0)',
                           paper_bgcolor='rgba(0,0,0,0)')
    # unselected_plot_df is gray background, no hover
    if background_data.shape[0] > 10:
        fig_gene.add_trace(
            go.Scattergl(
                x=background_data['x'],
                y=background_data['y'],
                mode='markers',
                name='Others',
                marker_size=n_cell_to_marker_size(background_data.shape[0]) - 1,
                marker_color='rgba(200, 200, 200, .5)',
                hoverinfo='skip')
        )
    # reorder data to put the background trace in first (bottom)
    fig_gene.data = fig_gene.data[::-1]

    return fig_cell_meta, fig_gene
