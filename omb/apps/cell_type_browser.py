from functools import lru_cache

import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots

from .default_values import *
from .sunburst import create_sunburst
from .utilities import n_cell_to_marker_size, get_split_plot_df
from ..app import app


def _make_cell_type_url_markdown(name, total_url):
    new_url = total_url.split('?')[0] + f'?ct={name.replace(" ", "%20")}'
    markdown = f'[{name}]({new_url})'
    return markdown


def _prepare_cell_type_markdown(cell_type_name, total_url):
    # name and stats
    cell_type_series = dataset.cell_type_table.loc[cell_type_name]
    cluster_size = cell_type_series['Number of total cells']

    try:
        cell_type_level = dataset.cluster_name_to_level[cell_type_name]
    except KeyError:
        return None

    # Parent
    if cell_type_level == 'CellClass':
        parent = '-'
        parent_url = 'None'
    else:
        parent = dataset.child_to_parent[cell_type_name]
        parent_url = _make_cell_type_url_markdown(parent, total_url)

    # Sibling
    sibling_urls = [_make_cell_type_url_markdown(ct, total_url)
                    for ct in dataset.parent_to_children_list[parent]
                    if ct != cell_type_name]
    sibling_url_str = ',\n'.join(sibling_urls)
    if sibling_url_str == '':
        sibling_url_str = 'None'

    # Children
    try:
        children_urls = [_make_cell_type_url_markdown(ct, total_url)
                         for ct in dataset.parent_to_children_list[cell_type_name]]
        children_urls_str = ',\n'.join(children_urls)
    except KeyError:
        # no children
        children_urls_str = 'None'

    cell_type_markdown = f"""
**Number of Nuclei**: {cluster_size}

**Parent**: {parent_url}

**Sibling(s)**: 

{sibling_url_str}

**Child(ren)**: 

{children_urls_str}

**Description**: 
"""
    return cell_type_markdown


TOTAL_GENE_OPTIONS = [{'label': gene_name, 'value': gene_int}
                      for gene_int, gene_name in
                      dataset.gene_meta_table['gene_name'].iteritems()]


def create_cell_type_browser_layout(cell_type_name, total_url):
    cell_type_name = cell_type_name.replace('_', ' ')
    cell_type_name = cell_type_name.replace('%20', ' ')

    cluster_level = dataset.cluster_name_to_level[cell_type_name]
    occur_coords = [k for k, v in dataset.coord_cell_type_occur.items() if cell_type_name in v]
    coord_and_cluster_levels = [f"{coord} - {'SubType' if coord.startswith('L3') else 'MajorType'}"
                                for coord in occur_coords]
    if cluster_level == 'CellClass':
        default_choice = 'L1UMAP - MajorType'
    elif cluster_level == 'MajorType':
        default_choice = [x for x in coord_and_cluster_levels if x.startswith('L2UMAP')][
            0]  # should only have one choice
    else:
        default_choice = [x for x in coord_and_cluster_levels if x.startswith('L3UMAP')][
            0]  # should only have one choice

    cell_type_markdown = _prepare_cell_type_markdown(cell_type_name, total_url)

    layout = html.Div(children=[
        # first row is cell_type_card and region_compo_sunburst
        html.Div(
            children=[
                html.Div(children=[
                    html.H6(children=cell_type_name, id='cell_type_name'),
                    dcc.Markdown(cell_type_markdown, id='cell_mark_down'),
                ], className='pretty_container three columns'),
                html.Div(children=[
                    html.H6('Mapping Metrics'),
                    dcc.Graph(id='metric_violin',
                              config={'displayModeBar': False})
                ], className='pretty_container three columns'),
                html.Div(children=[
                    html.H6('Dissection Region'),
                    dcc.Graph(id='region_bar_plot',
                              config={'displayModeBar': False},
                              style={'overflowY': 'scroll', 'height': 450})
                ], className='pretty_container two columns'),
                html.Div(children=[
                    html.H6('Brain Region Composition'),
                    dcc.Graph(id='region_sunburst')
                ], className='pretty_container four columns')
            ],
            className='row container-display'
        ),

        # second row has two scatter plots that can be plotted differently
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H6('Scatter Control'),
                        html.H6('Layout',
                                className="control_label"),
                        dcc.Dropdown(
                            options=[{'label': coord_and_level, 'value': coord_and_level}
                                     for coord_and_level in coord_and_cluster_levels],
                            clearable=False,
                            value=default_choice,
                            id='coords_cluster_level_dropdown',
                            className="dcc_control"),
                        html.H6('Gene Body of',
                                className="control_label"),
                        dcc.Dropdown(
                            clearable=False,
                            value=15397,  # TODO change a best default for each cluster
                            id='dynamic_gene_dropdown',
                            className="dcc_control"),
                        html.H6('Color By',
                                className="control_label"),
                        dcc.Dropdown(
                            options=[{'label': 'Norm. mCH / CH', 'value': 'CHN'},
                                     {'label': 'Norm. mCG / CG', 'value': 'CGN'}],
                            value='CHN',
                            clearable=False,
                            id='mc_type_dropdown',
                            className="dcc_control"),
                        html.H6('Color Range',
                                className="control_label"),
                        dcc.RangeSlider(
                            min=0,
                            max=3,
                            step=0.1,
                            marks={0: '0', 0.5: '0.5', 1: '1',
                                   1.5: '1.5', 2: '2', 2.5: '2.5',
                                   3: '3'},
                            value=[0.5, 1.5],
                            id='mc_range_slider',
                            className="dcc_control")
                    ],
                    id='scatter_control',
                    className='pretty_container two columns'),
                html.Div(
                    children=[
                        html.H6('Scatter Plot - Cell Type'),
                        dcc.Graph(id='scatter_plot_1',
                                  config={'displayModeBar': False})
                    ],
                    className='pretty_container four columns'
                ),
                html.Div(
                    children=[
                        html.H6('Scatter Plot - Gene Body +/- 2Kb mC Fraction'),
                        dcc.Graph(id='scatter_plot_2')
                    ],
                    className='pretty_container four columns'
                ),
                html.Div(
                    children=[
                        html.H6('mC Frac. Dist.'),
                        dcc.Graph(id='gene_violin',
                                  config={'displayModeBar': False})
                    ],
                    className='pretty_container two columns'
                ),
            ], className='row container-display'
        ),

        # third row is CH-DMG table
        html.Div(
            children=[
                # control panel of the dmg table
                html.Div(
                    children=[
                        html.P('Load preset or choose any cluster combination below'),
                        html.Div(
                            children=[
                                html.Button('Parent Marker', id='parent_marker_button', n_clicks=0),
                                html.Button('Sibling Marker', id='sibling_marker_button', n_clicks=0),
                            ],
                            className='row'
                        ),
                        html.P('Cluster set A (hypo-methylated)'),
                        html.Div(dcc.Dropdown(id='hypo_cluster_dropdown')),
                        html.P('Cluster set B (hyper-methylated)'),
                        html.Div(dcc.Dropdown(id='hyper_cluster_dropdown'))
                    ],
                    className='pretty_container three columns'
                ),
                # dmg table
                html.Div(
                    children=[
                        html.P('DMG Table'),
                        dash_table.DataTable(id='dmg_table')
                    ],
                    className='pretty_container nine columns'
                )
            ], className='row container-display'
        ),

        # fourth row contain gene scatter plot
        html.Div(children=[
            # some example layout
            html.Div(children=[
                html.Div(dcc.Graph(), className='pretty_container six columns'),
                html.Div(dcc.Graph(), className='pretty_container six columns'),
            ], className='row container-display'),
            html.Div(children=[
                html.Div(dcc.Graph(), className='pretty_container six columns'),
                html.Div(dcc.Graph(), className='pretty_container six columns'),
            ], className='row container-display'),
        ], id='dmg_box_plots')
    ])
    return layout


@lru_cache()
def _cell_type_name_to_cell_ids(cell_type_name, sample=None):
    cell_clusters = dataset.get_variables(
        dataset.cluster_name_to_level[cell_type_name])
    cell_clusters = cell_clusters[cell_clusters == cell_type_name]
    if (sample is not None) and (cell_clusters.size > sample):
        cell_clusters = cell_clusters.sample(sample, random_state=1)

    cell_ids = cell_clusters[cell_clusters == cell_type_name].index
    return cell_ids


@lru_cache()
@app.callback(
    Output('metric_violin', 'figure'),
    [Input('cell_type_name', 'children')]
)
def update_metric_violin(cell_type_name):
    cell_ids = _cell_type_name_to_cell_ids(cell_type_name, sample=10000)

    metric_df = dataset.get_variables(
        ['CG_RateAdj', 'CH_RateAdj', 'FinalReads', 'MappingRate']).loc[cell_ids]

    titles = ["Overall mCH / CH", "Overall mCG / CG", "Final Reads", "Mapping Rate"]

    fig = make_subplots(rows=4,
                        cols=1,
                        specs=[[{
                            "rowspan": 1
                        }], [{
                            "rowspan": 1
                        }], [{
                            "rowspan": 1
                        }], [{
                            "rowspan": 1
                        }]],
                        subplot_titles=titles)

    for row, ((_, data), title) in enumerate(zip(metric_df.iteritems(), titles)):
        fig.append_trace(go.Violin(
            x=data,
            orientation='h',
            points=False,
            meanline_visible=True,
            hoverinfo='none',
            side='positive',
            name=title
        ),
            row=row + 1,
            col=1)

    fig.update_layout(showlegend=False,
                      margin=dict(t=30, l=0, r=0, b=15),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(nticks=10)
    return fig


@app.callback(
    Output('region_bar_plot', 'figure'),
    [Input('cell_type_name', 'children')]
)
def update_region_bar_plot(cell_type_name):
    height_scale = 15
    cell_ids = _cell_type_name_to_cell_ids(cell_type_name)
    cell_disc_region = dataset.get_variables('RegionName').loc[cell_ids]
    disc_region_portion = cell_disc_region.astype(str).value_counts()
    disc_region_portion = disc_region_portion.reset_index()
    disc_region_portion.columns = ['Region Name', 'Count']
    disc_region_portion['Portion'] = disc_region_portion['Count'] / cell_ids.size
    disc_region_portion['Color'] = disc_region_portion['Region Name'].map(dataset.region_label_to_cemba_name).map(
        dataset.get_palette('Region'))
    fig = px.bar(disc_region_portion,
                 x='Portion',
                 y='Region Name',
                 hover_name='Region Name',
                 hover_data=['Count', 'Portion'],
                 color='Region Name',
                 color_discrete_sequence=disc_region_portion['Color'].tolist(),
                 orientation='h')
    fig.update_layout(showlegend=False,
                      yaxis=dict(dtick=1),
                      height=disc_region_portion.shape[0] * height_scale,  # show all label
                      margin=dict(t=30, l=0, r=0, b=15),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>'
                      '<b>Count: </b>%{customdata[0]}<br>'
                      '<b>Portion: </b>%{customdata[1]:.3f}')
    return fig


@app.callback(
    Output('region_sunburst', 'figure'),
    [Input('cell_type_name', 'children')]
)
def update_sunburst(cell_type_name):
    cell_ids = _cell_type_name_to_cell_ids(cell_type_name)
    fig = create_sunburst(levels=REGION_LEVELS, selected_cells=cell_ids)
    return fig


@app.callback(
    Output('dynamic_gene_dropdown', 'options'),
    [Input('dynamic_gene_dropdown', 'search_value')]
)
def update_gene_options(search_value):
    if not search_value:
        raise PreventUpdate

    this_options = [o for o in TOTAL_GENE_OPTIONS if search_value in o["label"]]
    if len(this_options) > 100:
        return [{'label': 'Keep typing...', 'value': 'NOT A GENE', 'disabled': True}]
    else:
        return this_options


def generate_cell_type_scatter(selected_plot_df, unselected_plot_df, hue, palette, hover_name, hover_cols):
    # selected_plot_df is colored and hover_data
    fig = px.scatter(selected_plot_df,
                     x="x",
                     y="y",
                     color=hue,
                     color_discrete_map=palette,
                     hover_name=hover_name,
                     hover_data=hover_cols)
    fig.update_layout(showlegend=False,
                      margin=dict(t=15, l=0, r=0, b=15),
                      xaxis=go.layout.XAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      yaxis=go.layout.YAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')

    # update marker size and hover template
    fig.update_traces(mode='markers',
                      marker_size=n_cell_to_marker_size(selected_plot_df.shape[0]),
                      hovertemplate='<b>%{hovertext}</b><br>'
                                    '<b>Dissection Region: </b>%{customdata[0]}<br>'
                                    '<b>SubType: </b>%{customdata[1]}')

    # unselected_plot_df is gray background, no color
    if unselected_plot_df.shape[0] > 100:
        fig.add_trace(
            go.Scattergl(
                x=unselected_plot_df['x'],
                y=unselected_plot_df['y'],
                mode='markers',
                marker_size=n_cell_to_marker_size(unselected_plot_df.shape[0]) - 1,
                marker_color='rgba(200, 200, 200, .5)',
                text=unselected_plot_df[hue],
                name='',
                hovertemplate='<b>Background</b>: %{text}'
            )
        )
    # reorder data to put the background trace in first (bottom)
    fig.data = fig.data[::-1]
    return fig


def generate_gene_scatter(plot_df, hue, hue_norm, hover_name, hover_cols):
    # selected_plot_df is colored and hover_data
    fig = px.scatter(plot_df,
                     x="x",
                     y="y",
                     color=hue,
                     range_color=hue_norm,
                     color_continuous_scale='Viridis',
                     hover_name=hover_name,
                     hover_data=hover_cols)
    fig.update_layout(showlegend=False,
                      margin=dict(t=15, l=0, r=0, b=15),
                      xaxis=go.layout.XAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      yaxis=go.layout.YAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')

    # update marker size and hover template
    fig.update_traces(mode='markers',
                      marker_size=n_cell_to_marker_size(plot_df.shape[0]),
                      hovertemplate='<b>%{hovertext}</b><br>'
                                    '<b>Dissection Region: </b>%{customdata[0]}<br>'
                                    '<b>SubType: </b>%{customdata[1]}')
    return fig


def _prepare_for_both_scatter(coord_and_cell_type_level, cell_type_name):
    try:
        coord_base, cell_type_level = coord_and_cell_type_level.split(' - ')
    except ValueError:
        raise PreventUpdate

    selected_cells = _cell_type_name_to_cell_ids(cell_type_name)

    selected_plot_df, unselected_plot_df, hover_cols, palette = get_split_plot_df(
        coord_base=coord_base,
        variable_name=cell_type_level,
        selected_cells=selected_cells,
        hover_cols=('RegionName', 'SubType'))

    if selected_plot_df.shape[0] > DOWN_SAMPLE:
        selected_plot_df = selected_plot_df.sample(DOWN_SAMPLE, random_state=0)
    if unselected_plot_df.shape[0] > DOWN_SAMPLE:
        unselected_plot_df = unselected_plot_df.sample(DOWN_SAMPLE, random_state=0)
    return selected_plot_df, unselected_plot_df, cell_type_level, palette, hover_cols


@app.callback(
    Output('scatter_plot_1', 'figure'),
    [Input('coords_cluster_level_dropdown', 'value')],
    [State('cell_type_name', 'children')]
)
def update_scatter_plot_1(coord_and_cell_type_level, cell_type_name):
    selected_plot_df, unselected_plot_df, cell_type_level, palette, hover_cols = _prepare_for_both_scatter(
        coord_and_cell_type_level, cell_type_name)
    # make figure
    fig = generate_cell_type_scatter(
        selected_plot_df,
        unselected_plot_df,
        hue=cell_type_level,
        palette=palette,
        hover_name=cell_type_level,
        hover_cols=hover_cols)
    return fig


@app.callback(
    [Output('scatter_plot_2', 'figure'),
     Output('gene_violin', 'figure')],
    [Input('coords_cluster_level_dropdown', 'value'),
     Input('dynamic_gene_dropdown', 'value'),
     Input('mc_type_dropdown', 'value'),
     Input('mc_range_slider', 'value')],
    [State('cell_type_name', 'children')]
)
def update_scatter_plot_1(coord_and_cell_type_level, gene_int, mc_type, hue_norm, cell_type_name):
    gene_name = dataset.gene_meta_table.loc[gene_int, 'gene_name']

    if not gene_int:
        raise PreventUpdate
    selected_plot_df, unselected_plot_df, cell_type_level, palette, hover_cols = _prepare_for_both_scatter(
        coord_and_cell_type_level, cell_type_name)

    gene_data = dataset.get_gene_rate(gene=gene_int, mc_type=mc_type)
    selected_plot_df[gene_name] = gene_data.reindex(selected_plot_df.index)
    unselected_plot_df[gene_name] = gene_data.reindex(unselected_plot_df.index)

    scatter_fig = generate_gene_scatter(
        pd.concat([selected_plot_df, unselected_plot_df]),
        hue=gene_name,
        hue_norm=hue_norm,
        hover_name=cell_type_level,
        hover_cols=hover_cols)

    # update gene violin
    violin_fig = go.Figure()
    # must recalculate level based on the cell type name, the above one is for coords
    _this_cell_type_level = dataset.cluster_name_to_level[cell_type_name]
    violin_fig.add_trace(go.Violin(y=selected_plot_df[gene_name],
                                   legendgroup='-',
                                   scalegroup='-',
                                   name='Cell Type vs Background',
                                   points=False,
                                   side='negative',
                                   hoverinfo='skip',
                                   line_color=dataset.get_palette(_this_cell_type_level)[cell_type_name]))
    violin_fig.add_trace(go.Violin(y=unselected_plot_df[gene_name],
                                   legendgroup='-',
                                   scalegroup='-',
                                   name='Cell Type vs Background',
                                   side='positive',
                                   points=False,
                                   hoverinfo='skip',
                                   line_color='lightgray'))
    violin_fig.update_traces(meanline_visible=True,
                             showlegend=False)
    violin_fig.update_layout(violingap=0,
                             violinmode='overlay',
                             margin=dict(t=30, l=0, r=0, b=15),
                             plot_bgcolor='rgba(0,0,0,0)',
                             paper_bgcolor='rgba(0,0,0,0)')
    violin_fig.update_xaxes(range=[-0.5, 0.5])
    violin_fig.update_yaxes(range=[0, 3])
    return scatter_fig, violin_fig
