from functools import lru_cache

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from .default_values import *
from .utilities import n_cell_to_marker_size
from ..app import app, APP_ROOT_NAME

CELL_TYPE_COUNTS = dataset.cell_type_table['Cluster Level'].value_counts().to_dict()
CELL_TYPE_COUNTS.update(dataset.cell_type_table['Parent'].value_counts().to_dict())
CELL_TYPE_COUNTS.update({'Sub-All': 161, 'Sub-Exc': 68, 'Sub-Inh': 77, 'Sub-NonN': 16})


def get_gene_info_markdown(gene_int):
    gene_info = dataset.gene_meta_table.loc[gene_int].to_dict()

    # prepare external URL
    mgi_id = gene_info['mgi_id']
    mgi_url = f'http://www.informatics.jax.org/marker/{mgi_id}' if mgi_id != '-' else None
    mgi_str = f'- **MGI**: [{mgi_id}]({mgi_url})' if mgi_url else ''

    entrez_id = gene_info['entrez_id']
    entrez_url = f'http://www.ncbi.nlm.nih.gov/gene/{entrez_id}' if entrez_id != '-' else None
    entrez_str = f'- **NCBI Gene**: [{entrez_id}]({entrez_url})' if entrez_url else ''

    allen_id = gene_info['allen_ish_internal_gene_id']
    allen_url = f'http://mouse.brain-map.org/gene/show/{allen_id}' if allen_id != '-' else None
    allen_str = f'- **Allen ISH Experiments**: [{allen_id}]({allen_url})' if allen_url else ''

    ensembl_id = gene_info['gene_id']
    ensembl_url = f'http://www.ensembl.org/Mus_musculus/geneview?gene={ensembl_id.split(".")[0]}'

    phenotype_str = gene_info['gene_phenotype']
    if phenotype_str != '-':
        phenotypes = phenotype_str.split(', ')
        n_phenotypes = len(phenotypes)
        if n_phenotypes > 10:
            phenotype_str = ', '.join(phenotypes[:10]) + \
                            f'... (see remaining items in the Ensembl Database)'
    else:
        phenotype_str = 'None'

    # assemble everything
    markdown = f"""
**Description**: {gene_info['gene_description'].replace('[', '(').replace(']', ')')}

**Location**: {gene_info['chrom']}:{gene_info['start']}-{gene_info['end']}, {'forward' if gene_info['strand'] == '+' else 'reverse'} strand.

**Gene Body Length**: {int(gene_info['end'] - gene_info['start'])} bp

**Gene Type**: {gene_info['gene_type'].replace('_', ' ').capitalize()}

**Phenotype (Ensembl)**: {phenotype_str}

**More Details in the External Databases**:
- **ENSEMBL**: [{ensembl_id}]({ensembl_url})
{mgi_str}
{entrez_str}
{allen_str}
"""
    return markdown


def standardize_gene(gene):
    try:
        gene_int = int(gene)
        gene_id = GENE_META_DF.loc[gene_int, 'gene_id']
        gene_name = GENE_META_DF.loc[gene_int, 'gene_name']
    except ValueError:
        if gene in dataset.gene_name_to_int:
            gene_name = gene
            gene_int = dataset.gene_name_to_int[gene_name]
            gene_id = GENE_META_DF.loc[gene_int, 'gene_id']
        elif gene in dataset.gene_id_to_int:
            gene_id = gene
            gene_int = dataset.gene_id_to_int[gene_id]
            gene_name = GENE_META_DF.loc[gene_int, 'gene_name']
        else:
            return None, None, None
    return gene_int, gene_id, gene_name


CELL_TYPES = dataset.cell_type_table
CLUSTER_DICT = {parent: sub_df['Number of total cells']  # series of subtype cell numbers
                for parent, sub_df in CELL_TYPES[CELL_TYPES['Cluster Level'] == 'SubType'].groupby('Parent')}


def create_gene_browser_layout(gene):
    gene_int, gene_id, gene_name = standardize_gene(gene)
    if gene_int is None:
        return None

    first_row = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Jumbotron(
                        [
                            html.H1(gene_name, id='gene_name'),
                            html.P(gene_int, id='gene_int', hidden=True),
                            dcc.Markdown(id='gene_contents',
                                         children=get_gene_info_markdown(gene_int))
                        ],
                        className='p-4 m-0 h-100'
                    )
                ],
                width=12, lg=6
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Gene - Cell Type Box Plot'),
                            dbc.CardBody(
                                [
                                    dbc.Form(
                                        [
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label('Select Cell Type Level',
                                                              className='mr-3'),
                                                    dcc.Dropdown(
                                                        id='box-plot-level-dropdown',
                                                        options=[{'label': 'CellClass', 'value': 'CellClass'},
                                                                 {'label': 'MajorType', 'value': 'MajorType'},
                                                                 {'label': 'SubType', 'value': 'SubType'}],
                                                        value='MajorType',
                                                        clearable=False,
                                                        style={'width': '250px'}
                                                    )
                                                ]
                                            )
                                        ],
                                        inline=True
                                    ),
                                    dcc.Loading(
                                        [
                                            dcc.Graph(id='gene-box-plot',
                                                      config={'displayModeBar': False})
                                        ]
                                    )
                                ]
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, lg=6
            )
        ],
        className='w-100'
    )

    control_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Coordinates', html_for='coords-dropdown'),
                    dcc.Dropdown(
                        id='coords-dropdown',
                        options=[{'label': name, 'value': name}
                                 for name in dataset.coord_names],
                        value='L1UMAP',
                        clearable=False
                    ),
                    dbc.FormText('Coordinates of both scatter plots.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Cell Metadata', html_for="cell-meta-dropdown"),
                    dcc.Dropdown(
                        options=[{'label': name, 'value': name}
                                 for name in CONTINUOUS_VAR + CATEGORICAL_VAR],
                        value='MajorType',
                        id="cell-meta-dropdown",
                        clearable=False),
                    dbc.FormText('Color of the left scatter plot.')
                ]
            ),
            html.Hr(className='my-2'),
            dbc.FormGroup(
                [
                    dbc.Label('Gene Body mC Type', html_for='mc-type-dropdown'),
                    dcc.Dropdown(
                        id='mc-type-dropdown',
                        options=[{'label': 'Norm. mCH / CH', 'value': 'CHN'},
                                 {'label': 'Norm. mCG / CG', 'value': 'CGN'}],
                        value='CHN',
                        clearable=False
                    ),
                    dbc.FormText('Color of the right scatter plot, '
                                 'using per cell normalized mCH or mCG fraction of the gene body.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Gene Color Scale', html_for='mc-range-slider'),
                    dcc.RangeSlider(
                        min=0,
                        max=3,
                        step=0.1,
                        marks={0: '0', 0.5: '0.5', 1: '1',
                               1.5: '1.5', 2: '2', 2.5: '2.5',
                               3: '3'},
                        value=[0.5, 1.5],
                        id='mc-range-slider',
                        className="dcc_control"),
                    dbc.FormText('Color scale of the right scatter plot.')
                ]
            ),
            html.Hr(className='my-2'),
            dcc.Markdown(id='gene-browser-pair-scatter-markdown')
        ]
    )

    second_row = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Scatter Control'),
                            dbc.CardBody(
                                [
                                    control_form
                                ]
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, xl=2
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Cell Metadata Scatter'),
                            dbc.CardBody(
                                [
                                    dcc.Loading(
                                        [
                                            dcc.Graph(id='cell-meta-scatter-plot',
                                                      style={"height": "65vh", "width": "auto"})
                                        ]
                                    ),
                                ]
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, xl=5
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Gene Scatter'),
                            dbc.CardBody(
                                [
                                    dcc.Loading(
                                        [
                                            dcc.Graph(id='gene-scatter-plot',
                                                      style={"height": "65vh", "width": "auto"})
                                        ]
                                    )
                                ]
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, xl=5
            )
        ],
        className='my-4'
    )

    clusters_with_track = [c for c in dataset.cell_type_table.index if c in dataset.cell_type_to_annoj_track_id]
    cell_counts = dataset.get_variables('MajorType').value_counts().to_dict()
    cell_counts.update(dataset.get_variables('SubType').value_counts().to_dict())

    third_row = dbc.Card(
        [
            dbc.CardHeader('Genome Browser'),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5('View Genome Tracks in The AnnoJ Browser', className='card-title'),
                                    html.P('Control the browser layout and active tracks below, '
                                           'then click the button on the right to view the AnnoJ browser')
                                ]
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        'Update Browser Here',
                                        id='update-browser',
                                        className='mx-5'),
                                    dbc.Button(
                                        'Open In A New Tab',
                                        id='whole-page-link',
                                        target='_blank',  # open whole page in a new browser tab
                                    )
                                ],
                                className='h-100 p-3 m-auto'
                            )
                        ]
                    ),
                    html.Hr(className='mb-2'),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Form(
                                        [
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label('Track mC Type'),
                                                    dcc.Dropdown(
                                                        id='browser-mc-type-dropdown',
                                                        options=[{'label': 'mCH / CH', 'value': 'CH'},
                                                                 {'label': 'mCG / CG', 'value': 'CG'},
                                                                 {'label': 'Coverage', 'value': 'cov'}],
                                                        value='CH',
                                                        clearable=False
                                                    ),
                                                    dbc.FormText('Display mCH or mCG tracks of '
                                                                 'each selected cell type.')
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                width=12, lg=2
                            ),
                            dbc.Col(
                                [
                                    dbc.Form(
                                        [
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label('Browser Layout'),
                                                    dbc.Checklist(
                                                        id='browser-layout-checklist',
                                                        options=[
                                                            {'label': 'Color By Cell Type',
                                                             'value': 'cell_type_color'},
                                                            {'label': 'Hide Sidebar', 'value': 'sidebar'},
                                                            {'label': 'Hide Toolbar', 'value': 'toolbar'}
                                                        ],
                                                        value=['cell_type_color', 'sidebar']
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                width=12, lg=2
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Form(
                                                [
                                                    dbc.FormGroup(
                                                        [

                                                            dbc.Label('Select Tracks'),
                                                            dcc.Dropdown(
                                                                id='cell-type-track-dropdown',
                                                                options=[
                                                                    {'label': f'{ct} ({cell_counts[ct]} cells)',
                                                                     'value': ct}
                                                                    for ct in clusters_with_track],
                                                                multi=True,
                                                                value=[],
                                                            ),
                                                            dbc.FormText('Select tracks to view their methylation '
                                                                         'level around this gene.')
                                                        ]
                                                    )
                                                ],
                                                className='w-100'
                                            )
                                        ]
                                    ),
                                    dbc.Collapse(
                                        dbc.Row(
                                            [
                                                html.P('Warning: Loading too many tracks will be quite slow.',
                                                       className='text-danger my-auto')
                                            ],
                                            className='my-3'
                                        ),
                                        id='too-much-tracks'
                                    ),
                                    dbc.Row(
                                        [
                                            html.H6(
                                                'Load multiple MajorType tracks:',
                                                className='my-auto'
                                            ),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(f'ALL ({CELL_TYPE_COUNTS["MajorType"]})',
                                                               id='btn-major-tracks'),
                                                    dbc.Button(f'Exc ({CELL_TYPE_COUNTS["Exc"]})',
                                                               id='btn-major-exc-tracks'),
                                                    dbc.Button(f'Inh ({CELL_TYPE_COUNTS["Inh"]})',
                                                               id='btn-major-inh-tracks'),
                                                    dbc.Button(f'NonN ({CELL_TYPE_COUNTS["NonN"]})',
                                                               id='btn-major-non-tracks'),
                                                ],
                                                size='sm',
                                                className='align-middle ml-4'
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            html.H6('Load multiple SubType tracks:',
                                                    className='my-auto'
                                                    ),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(f'Exc ({CELL_TYPE_COUNTS["Sub-Exc"]})',
                                                               id='btn-sub-exc-tracks'),
                                                    dbc.Button(f'Inh ({CELL_TYPE_COUNTS["Sub-Inh"]})',
                                                               id='btn-sub-inh-tracks'),
                                                    dbc.Button(f'NonN ({CELL_TYPE_COUNTS["Sub-NonN"]})',
                                                               id='btn-sub-non-tracks'),
                                                ],
                                                size='sm',
                                                className='align-middle mx-4'
                                            )
                                        ],
                                        className='my-3'
                                    )
                                ],
                                width=12, lg=8
                            )
                        ],
                        form=True
                    ),
                    html.P('', id='iframe-url', hidden=True),
                    dbc.Collapse(
                        [
                            html.Hr(className='mb-3'),
                            html.Iframe(id='annoj-iframe',
                                        style={'width': '100%', 'height': '85vh'})
                        ],
                        className='w-100 m-0 p-0',
                        id='browser_collapse'
                    )
                ]
            )
        ],
        className='mt-4',
        style={'margin-bottom': '300px'}
    )

    layout = html.Div(
        children=[
            # first row is gene info and violin plot
            first_row,
            # second row is control panel and gene scatter
            second_row,
            # third row is annoj browser control
            third_row
        ]
    )
    return layout


@lru_cache()
@app.callback(
    Output('gene-box-plot', 'figure'),
    [Input('gene_int', 'children'),
     Input('mc-type-dropdown', 'value'),
     Input('box-plot-level-dropdown', 'value')],
    [State('gene_name', 'children')]
)
def update_box_plot(gene_int, mc_type, cell_type_level, gene_name):
    gene_data = dataset.get_gene_rate(gene_int=gene_int, mc_type=mc_type).copy()

    plot_data = pd.DataFrame({gene_name: gene_data})
    plot_data[cell_type_level] = dataset.get_variables(cell_type_level).astype(str)
    plot_data = plot_data[plot_data[cell_type_level].apply(lambda i: 'Outlier' not in i)].copy()

    # clip outliers to make y range smaller
    clip_on = 3
    plot_data.loc[plot_data[gene_name] > clip_on, gene_name] = clip_on

    # order cluster by median
    cluster_order = plot_data.groupby(cell_type_level)[gene_name].median().sort_values().index

    fig = go.Figure()
    palette = dataset.get_palette(cell_type_level)
    for cluster in cluster_order:
        this_data = plot_data[plot_data[cell_type_level] == cluster]
        fig.add_trace(go.Box(
            y=this_data[gene_name],
            boxpoints=False,
            orientation='v', name=cluster, marker_color=palette[cluster]))

    fig.update_layout(showlegend=False,
                      margin=dict(t=30, l=0, r=0, b=15),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    fig.update_yaxes(title='Gene Norm. mCH / CH')
    return fig


@app.callback(
    [Output('iframe-url', 'children'),
     Output('whole-page-link', 'href')],
    [Input('browser-mc-type-dropdown', 'value'),
     Input('browser-layout-checklist', 'value'),
     Input('gene_int', 'children'),
     Input('cell-type-track-dropdown', 'value')],
)
def update_url(mc_type, layout, gene_int, active_clusters):
    chrom, start, end = dataset.gene_meta_table.loc[gene_int, ['chrom', 'start', 'end']]

    iframe_url = dataset.annoj_url(
        active_clusters,
        chrom,
        start,
        end,
        track_type=mc_type,
        mc_track_height=50,
        hide_sidebar='sidebar' in layout,
        hide_toolbar='toolbar' in layout,
        cell_type_color='cell_type_color' in layout)

    whole_page_url = dataset.annoj_url(
        active_clusters,
        chrom,
        start,
        end,
        track_type=mc_type,
        mc_track_height=50,
        hide_sidebar=False,
        hide_toolbar=False,
        cell_type_color='cell_type_color' in layout)

    return iframe_url, whole_page_url


@app.callback(
    Output('annoj-iframe', 'src'),
    [Input('update-browser', 'n_clicks')],
    [State('iframe-url', 'children')]
)
def update_iframe(n_clicks, url):
    if not n_clicks:
        raise PreventUpdate
    return url


@app.callback(
    Output('browser_collapse', 'is_open'),
    [Input('update-browser', 'n_clicks')],
    [State('cell-type-track-dropdown', 'value')]
)
def toggle_collapse(n_clicks, active_clusters):
    if n_clicks and (len(active_clusters) != 0):
        return True
    else:
        return False


@app.callback(
    Output('cell-meta-scatter-plot', 'figure'),
    [Input('cell-meta-dropdown', 'value'),
     Input('coords-dropdown', 'value')]
)
def get_cell_meta_scatter_fig(var_name, coord_name):
    data = dataset.get_coords(coord_name)
    data[var_name] = dataset.get_variables(var_name)
    if var_name != 'SubType':
        data['SubType'] = dataset.get_variables('SubType')

    sample = 10000
    _data = data if data.shape[0] <= sample else data.sample(sample, random_state=0)

    # cell meta figure
    if var_name in CONTINUOUS_VAR:
        hue_norm = CONTINUOUS_VAR_NORMS.get(var_name, None)
        data[var_name] = data[var_name].astype(float)
        fig_cell_meta = px.scatter(data_frame=_data,
                                   x='x',
                                   y='y',
                                   color=var_name,
                                   range_color=hue_norm,
                                   color_continuous_scale='Viridis',
                                   hover_name='SubType',
                                   hover_data=[var_name])
        # update marker size and hover template
        fig_cell_meta.update_traces(mode='markers',
                                    marker_size=n_cell_to_marker_size(
                                        _data.shape[0]),
                                    hovertemplate='<b>%{hovertext}</b><br>'
                                                  f'<b>{var_name}: </b>%{{customdata[0]:.3f}}')
    else:
        data[var_name] = data[var_name]
        fig_cell_meta = px.scatter(
            _data,
            x="x",
            y="y",
            color=var_name,
            color_discrete_map=dataset.get_palette(var_name),
            hover_name='SubType',
            hover_data=[var_name])
        # update marker size and hover template
        fig_cell_meta.update_traces(mode='markers',
                                    marker_size=n_cell_to_marker_size(
                                        _data.shape[0]),
                                    hovertemplate='<b>%{hovertext}</b><br>')

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

    return fig_cell_meta


@app.callback(
    Output('gene-scatter-plot', 'figure'),
    [Input('coords-dropdown', 'value'),
     Input('gene_int', 'children'),
     Input('mc-type-dropdown', 'value'),
     Input('mc-range-slider', 'value')],
    [State('gene_name', 'children')]
)
def get_gene_scatter_fig(coord_name, gene_int, mc_type, cnorm, gene_name):
    data = dataset.get_coords(coord_name)
    data['SubType'] = dataset.get_variables('SubType')

    gene_col_name = f'{gene_name} m{mc_type[:-1]}'
    data[gene_col_name] = dataset.get_gene_rate(gene_int, mc_type)

    sample = 10000
    _data = data if data.shape[0] <= sample else data.sample(sample, random_state=0)

    # gene figure
    fig_gene = px.scatter(data_frame=_data,
                          x='x',
                          y='y',
                          color=gene_col_name,
                          range_color=cnorm,
                          color_continuous_scale='Viridis',
                          hover_name='SubType',
                          hover_data=[gene_col_name])
    # update marker size and hover template
    fig_gene.update_traces(mode='markers',
                           marker_size=n_cell_to_marker_size(_data.shape[0]),
                           hovertemplate='<b>%{hovertext}</b><br>'
                                         f'<b>{gene_col_name}: </b>%{{customdata[0]:.3f}}')

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
    return fig_gene


@app.callback(
    Output('gene-browser-pair-scatter-markdown', 'children'),
    [Input('coords-dropdown', 'value'),
     Input('cell-meta-dropdown', 'value'),
     Input('gene_name', 'children'),
     Input('mc-type-dropdown', 'value'),
     Input('mc-range-slider', 'value')]
)
def make_pair_scatter_markdown(coords, cell_meta, gene, mc_type, cnorm):
    url = f'/{APP_ROOT_NAME}scatter?coords={coords};meta={cell_meta};' \
          f'gene={gene};mc={mc_type};cnorm={",".join(map(str, cnorm))}'
    text = f'For more details, go to the [**Paired Scatter Browser**]({url.replace(" ", "%20")})'
    return text


@app.callback(
    Output('cell-type-track-dropdown', 'value'),
    [Input('btn-major-tracks', 'n_clicks'),
     Input('btn-major-exc-tracks', 'n_clicks'),
     Input('btn-major-inh-tracks', 'n_clicks'),
     Input('btn-major-non-tracks', 'n_clicks'),
     Input('btn-sub-exc-tracks', 'n_clicks'),
     Input('btn-sub-inh-tracks', 'n_clicks'),
     Input('btn-sub-non-tracks', 'n_clicks')],
    [State('cell-type-track-dropdown', 'value')]
)
def load_multiple_tracks(btn1, btn2, btn3, btn4,
                         btn6, btn7, btn8,  # can't use * here... call back do not set key_wd
                         cur_value):
    ctx = callback_context

    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'btn-major-tracks':
        cur_value += dataset.parent_to_children_list['Exc']
        cur_value += dataset.parent_to_children_list['Inh']
        cur_value += dataset.parent_to_children_list['NonN']
    elif button_id == 'btn-major-exc-tracks':
        cur_value += dataset.parent_to_children_list['Exc']
    elif button_id == 'btn-major-inh-tracks':
        cur_value += dataset.parent_to_children_list['Inh']
    elif button_id == 'btn-major-non-tracks':
        cur_value += dataset.parent_to_children_list['NonN']
    elif button_id == 'btn-sub-exc-tracks':
        cur_value += dataset.cluster_name_to_subtype('Exc')
    elif button_id == 'btn-sub-inh-tracks':
        cur_value += dataset.cluster_name_to_subtype('Inh')
    elif button_id == 'btn-sub-non-tracks':
        cur_value += dataset.cluster_name_to_subtype('NonN')

    cur_value = list(sorted(set(cur_value)))
    return cur_value


@app.callback(
    Output('too-much-tracks', 'is_open'),
    [Input('cell-type-track-dropdown', 'value')]
)
def too_much_tracks_warning(cur_value):
    if len(cur_value) > 15:
        return True
    else:
        return False
