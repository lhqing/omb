from functools import lru_cache

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from .default_values import *
from .utilities import n_cell_to_marker_size
from ..app import app

GENE_META_DF = dataset.gene_meta_table
MAX_TRACKS = 12
CATEGORICAL_VAR = [
    'RegionName', 'MajorRegion', 'SubRegion', 'CellClass', 'MajorType',
    'SubType'
]

CONTINUOUS_VAR = [
    'CCC_Rate', 'CG_Rate', 'CG_RateAdj', 'CH_Rate', 'CH_RateAdj',
    'FinalReads', 'InputReads', 'MappedReads', 'BamFilteringRate',
    'MappingRate', 'Slice'
]

CONTINUOUS_VAR_NORMS = {
    'CCC_Rate': (0, 0.02),
    'CG_Rate': (0.65, 0.85),
    'CG_RateAdj': (0.65, 0.85),
    'CH_Rate': (0, 0.04),
    'CH_RateAdj': (0, 0.04),
    'FinalReads': (5e5, 2e6),
    'InputReads': (1e6, 5e6),
    'MappedReads': (5e5, 3e6),
    'BamFilteringRate': (0.5, 0.8),
    'MappingRate': (0.5, 0.8)
}


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

**Phenotype (Ensemble)**: {phenotype_str}

**More Details in the External Databases**:
- **ENSEMBL**: [{ensembl_id}]({ensembl_url})
{mgi_str}
{entrez_str}
{allen_str}
"""
    return markdown


def standardize_gene(gene):
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


def get_cell_type_check_box_children():
    n_col = 5
    total_items = sum([len(i) for i in CLUSTER_DICT.values()]) + 3 * len(CLUSTER_DICT)
    items_per_col = round(total_items / n_col) - 2

    # parent to subtype map
    check_box_div_children = []
    cur_div_children = []
    items_count = 0
    for parent, subtype_counts in CLUSTER_DICT.items():
        cur_div_children += [html.H6(
            children=parent),
            dcc.Checklist(
                options=[{'label': f'{subtype} ({number} cells)', 'value': subtype}
                         for subtype, number in subtype_counts.items()],
                value=[],
                id=parent + '-checkbox')]
        items_count += (3 + len(subtype_counts))
        if items_count > items_per_col:
            check_box_div_children.append(
                html.Div(cur_div_children, style={'float': 'left', 'width': '20%'}))
            cur_div_children = []
            items_count = 0

    # last col
    if len(cur_div_children) != 0:
        check_box_div_children.append(
            html.Div(cur_div_children, style={'float': 'left', 'width': '20%'}))
    return check_box_div_children


def create_gene_browser_layout(gene):
    gene_int, gene_id, gene_name = standardize_gene(gene)
    if gene_int is None:
        return None

    layout = html.Div(children=[
        # first row is gene info and violin plot
        html.Div(children=[
            html.Div(children=[
                html.H1(gene_name, id='gene_name'),
                html.P(gene_int, id='gene_int', hidden=True),
                dcc.Markdown(id='gene_contents', children=get_gene_info_markdown(gene_int)),
            ], className='pretty_container four columns'),
            html.Div(children=[
                html.Div(children=[
                    html.H6('Gene - Cell Type Violin Plot'),
                    dcc.Dropdown(
                        id='violin-level-dropdown',
                        options=[{'label': 'CellClass', 'value': 'CellClass'},
                                 {'label': 'MajorType', 'value': 'MajorType'},
                                 {'label': 'SubType', 'value': 'SubType'}],
                        value='MajorType',
                        clearable=False
                    ),
                ], className='row'),
                dcc.Graph(id='gene_violin_plot',
                          config={'displayModeBar': False})
            ], className='pretty_container eight columns')
        ], className='row container-display'),

        # second row is control panel and gene scatter
        html.Div(children=[
            html.Div(children=[
                html.H6('Scatter Plots Control'),
                html.P('Scatter Coords'),
                dcc.Dropdown(
                    id='coords-dropdown',
                    options=[{'label': name, 'value': name}
                             for name in dataset.coord_names],
                    value='L1UMAP',
                    clearable=False
                ),
                html.P('Metadata'),
                dcc.Dropdown(
                    options=[{'label': name, 'value': name}
                             for name in CONTINUOUS_VAR + CATEGORICAL_VAR],
                    value='MajorType',
                    id="cell-meta-dropdown",
                    clearable=False),
                html.Hr(),
                html.P('Gene mC Type'),
                dcc.Dropdown(
                    id='mc-type-dropdown',
                    options=[{'label': 'Norm. mCH / CH', 'value': 'CHN'},
                             {'label': 'Norm. mCG / CG', 'value': 'CGN'}],
                    value='CHN',
                    clearable=False
                ),
                html.P('Gene Scatter Color Range'),
                dcc.RangeSlider(
                    min=0,
                    max=3,
                    step=0.1,
                    marks={0: '0', 0.5: '0.5', 1: '1',
                           1.5: '1.5', 2: '2', 2.5: '2.5',
                           3: '3'},
                    value=[0.5, 1.5],
                    id='mc-range-slider',
                    className="dcc_control")
            ], className='pretty_container three columns'),
            html.Div(children=[
                html.H6('Cell Metadata Scatter Plot'),
                dcc.Graph(id='cell-meta-scatter-plot'),
            ], className='pretty_container five columns'),
            html.Div(children=[
                html.H6('Gene mC Rate Scatter Plot'),
                dcc.Graph(id='gene-scatter-plot'),
            ], className='pretty_container five columns'),
        ], className='row container-display'),

        # third row is annoj browser control
        html.Div(children=[
            dcc.Tabs(
                id='genome-browser-tabs',
                value='control-tab',
                children=[
                    dcc.Tab(
                        value='control-tab',
                        label='Genome Browser Control',
                        children=[
                            html.H5('View the Gene in the AnnoJ Browser'),
                            html.P('Control the layout and active tracks below, '
                                   'then click the "UPDATE BROWSER" button to view the AnnoJ browser, '
                                   'or click the "OPEN WHOLE PAGE BROWSER" to view in a new tab.'),
                            html.Hr(),
                            html.Div([
                                html.Div([
                                    html.H6('Track Data Type'),
                                    dcc.Dropdown(
                                        id='browser-mc-type-dropdown',
                                        options=[{'label': 'mCH / CH', 'value': 'CH'},
                                                 {'label': 'mCG / CG', 'value': 'CG'},
                                                 {'label': 'Coverage', 'value': 'cov'}],
                                        value='CH',
                                        clearable=False
                                    )], className='two columns'
                                ),
                                html.Div([
                                    html.H6('Browser Layout'),
                                    dcc.Checklist(
                                        id='browser-layout-checklist',
                                        options=[
                                            {'label': 'Color By Cell Type', 'value': 'cell_type_color'},
                                            {'label': 'Hide Sidebar', 'value': 'sidebar'},
                                            {'label': 'Hide Toolbar', 'value': 'toolbar'}
                                        ],
                                        value=['cell_type_color', 'sidebar']
                                    )], className='two columns'),
                                html.Button('Update Browser',
                                            id='update-browser',
                                            className='two columns'),
                                html.A(html.Button('Open Whole Page Browser'),
                                       id='whole_page_link',
                                       target='_blank',  # open whole page in a new browser tab
                                       className='two columns')
                            ], className='row'),
                            html.Hr(),
                            html.Div([
                                html.H6(f'Select at most {MAX_TRACKS} cell types'),
                                html.Div(get_cell_type_check_box_children())])
                        ]),
                    dcc.Tab(
                        value='browser-tab',
                        label='Genome Browser',
                        children=html.Div([
                            # url saved in this hidden P,
                            # only update when click the update button on control tab
                            html.P('', id='iframe_url', hidden=True),
                            html.Iframe(id='annoj-iframe',
                                        width='100%', height='800px',
                                        className='twelve columns')
                        ])
                    ),
                ], persistence=True),
        ], className='pretty_container twelve columns'),
    ])
    return layout


@lru_cache()
@app.callback(
    Output('gene_violin_plot', 'figure'),
    [Input('gene_int', 'children'),
     Input('mc-type-dropdown', 'value'),
     Input('violin-level-dropdown', 'value')],
    [State('gene_name', 'children')]
)
def update_metric_violin(gene_int, mc_type, cell_type_level, gene_name):
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
    return fig


@app.callback(
    [Output('iframe_url', 'children'),
     Output('whole_page_link', 'href')],
    [Input('browser-mc-type-dropdown', 'value'),
     Input('browser-layout-checklist', 'value'),
     Input('gene_int', 'children')] +
    [Input(f'{cluster}-checkbox', 'value') for cluster in CLUSTER_DICT.keys()],
)
def update_url(mc_type, layout, gene_int, *clusters):
    active_clusters = []
    for cluster_list in clusters:
        active_clusters += cluster_list
    active_clusters = active_clusters[:MAX_TRACKS]

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
    [Output('annoj-iframe', 'src'),
     Output('genome-browser-tabs', 'value')],
    [Input('update-browser', 'n_clicks')],
    [State('iframe_url', 'children')]
)
def update_iframe(n_clicks, url):
    if not n_clicks:
        raise PreventUpdate
    return url, 'browser-tab'


@app.callback(
    [Output('cell-meta-scatter-plot', 'figure'),
     Output('gene-scatter-plot', 'figure')],
    [Input('cell-meta-dropdown', 'value'),
     Input('coords-dropdown', 'value'),
     Input('gene_int', 'children'),
     Input('mc-type-dropdown', 'value')],
    [State('gene_name', 'children')]
)
def get_scatter_fig(var_name, coord_name, gene_int, mc_type, gene_name):
    data = dataset.get_coords(coord_name)
    data[var_name] = dataset.get_variables(var_name)
    if var_name != 'SubType':
        data['SubType'] = dataset.get_variables('SubType')

    gene_col_name = f'{gene_name} m{mc_type[:-1]}'
    data[gene_col_name] = dataset.get_gene_rate(gene_int, mc_type)

    sample = 10000
    _data = data if data.shape[0] <= sample else data.sample(sample)

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

    # gene figure
    fig_gene = px.scatter(data_frame=_data,
                          x='x',
                          y='y',
                          color=gene_col_name,
                          range_color=(0.5, 1.5),
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
    return fig_cell_meta, fig_gene
