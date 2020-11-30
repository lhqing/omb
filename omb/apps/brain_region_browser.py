from functools import lru_cache

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

from .default_values import *
from .sunburst import create_sunburst
from .utilities import n_cell_to_marker_size
from ..app import app, APP_ROOT_NAME


def _background_mesh(region_name, color=None, opacity=0.1):
    (x, y, z, i, j, k), region_name, region_type, region_color = dataset.read_ply(
        region_name)
    if color is None:
        color = region_color
    if region_name == 'root':
        region_name = 'Brain'
    data = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        # i, j and k give the vertices of triangles
        i=i,
        j=j,
        k=k,
        color=color,
        name=region_name,
        hoverinfo='skip',
        showlegend=True,
        opacity=opacity)
    return data


def _roi_mesh(region_name, color=None, hoverinfo='text+name', opacity=1):
    (x, y, z, i, j, k), region_name, region_type, region_color = dataset.read_ply(
        region_name)
    if color is None:
        color = region_color
    data = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        # i, j and k give the vertices of triangles
        i=i,
        j=j,
        k=k,
        color=color,
        text=region_type,
        name=region_name,
        hoverinfo=hoverinfo,
        showlegend=True,
        opacity=opacity)
    return data


def _get_valid_coords(region_name):
    dissection_regions = dataset.region_label_to_dissection_region_dict[region_name]
    region_and_subtype = dataset.get_variables(['RegionName', 'SubType'])
    occur_subtypes = set(region_and_subtype.loc[
                             region_and_subtype['RegionName'].isin(dissection_regions),
                             'SubType'].unique())
    valid_coords = [
        k for k, v in dataset.coord_cell_type_occur.items()
        if len(v & occur_subtypes) > 0
    ]
    return set(valid_coords)


def _brain_region_info_markdown(region_name):
    dissection_regions = dataset.region_label_to_dissection_region_dict[region_name]
    this_region_table = dataset.brain_region_table.loc[dissection_regions]

    n_cells = this_region_table['Number of total cells'].sum()
    n_region = this_region_table.shape[0]

    try:
        description = dataset.brain_region_acronym_to_name[region_name]
    except KeyError:
        description = ''
        print(region_name, 'not found')

    if n_region == 1:
        cemba_id = dataset.brain_region_table.loc[dissection_regions, 'Slice'].unique()[0]
        slice_str = f"**Cornal Slice**: {cemba_id}"
        cemba_id = dataset.brain_region_table.loc[dissection_regions, 'Dissection Region ID'].unique()[0]
        dissection_region_str = f"**Dissection Region ID**: {cemba_id}"

        potential_overlap = ','.join(this_region_table['Potential Overlap'].dropna().tolist()).replace(',', ', ')
        if potential_overlap != '':
            potential_overlap_str = f'**Potentially Overlap With**: {potential_overlap}'
        else:
            potential_overlap_str = ''
    else:
        slice_str = ''
        dissection_region_str = ''
        potential_overlap_str = ''

    anatomical_str = ''
    for major_region, sub_df in this_region_table.groupby('Major Region'):
        sub_region_str = ', '.join([f"[{r}](brain_region?br={r})" for r in sub_df['Sub-Region'].unique()])
        anatomical_str += f'- [{major_region}](brain_region?br={major_region}): {sub_region_str}\n'

    if region_name != 'ALL REGIONS':
        all_region_link = 'View [ALL](brain_region?br=ALL%20REGIONS) dissection regions.'
        if n_region > 1:
            dissection_region_list = ', '.join([f"[{r}](brain_region?br={r})" for r in dissection_regions])
            dissection_region_list_str = f'**Dissection Regions**: {dissection_region_list}'
        else:
            dissection_region_list_str = ''
    else:
        all_region_link = ''
        dissection_region_list_str = ''

    markdown = f"""
**Description**: {description}

**Number of Cells**: {n_cells} cells from {n_region} dissection region{"s" if n_region != 1 else ""}.

{dissection_region_str}

{slice_str}

**Dissected Anatomical Structures**: 
{anatomical_str}
{potential_overlap_str}

{dissection_region_list_str}

{all_region_link}
"""
    return markdown


def _default_ccf_mesh_selection(region_name):
    dissection_regions = dataset.region_label_to_dissection_region_dict[region_name]
    this_region_table = dataset.brain_region_table.loc[dissection_regions]

    if region_name == 'ALL REGIONS':
        include_regions = ['root'] + this_region_table['Major Region'].unique().tolist()
    else:
        include_regions = ['root'] + this_region_table['Sub-Region'].unique().tolist()

    if 'PFC' in include_regions:
        include_regions.remove('PFC')
        include_regions += ['ILA', 'PL']
    return include_regions


def create_brain_region_browser_layout(region_name):
    region_name = region_name.replace('%20', ' ')
    valid_coords = _get_valid_coords(region_name)
    if region_name not in dataset.region_label_to_dissection_region_dict:
        return None
    first_row = dbc.Row(
        [
            # brain region info
            dbc.Col(
                [
                    dbc.Jumbotron(
                        [
                            html.H1(region_name, id='region-name'),
                            dcc.Markdown(children=_brain_region_info_markdown(region_name))
                        ],
                        className='h-100'
                    )
                ],
                width=12, lg=3
            ),
            # 3D mesh control
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('3D Mesh Control'),
                            dbc.CardBody(
                                [
                                    dbc.FormGroup(
                                        [
                                            dbc.Label('Dissection Regions', html_for='cemba-mesh-dropdown'),
                                            dcc.Dropdown(
                                                options=[
                                                    {'label': region,
                                                     'value': region}
                                                    for region in
                                                    dataset.region_label_to_dissection_region_dict.keys()],
                                                id="cemba-mesh-dropdown",
                                                value=[region_name],
                                                multi=True),
                                            dbc.FormText('Load dissection regions from this study.')
                                        ]
                                    ),
                                    html.Hr(className='my-3'),
                                    dbc.FormGroup(
                                        [
                                            dbc.Label('Anatomical Structures',
                                                      html_for="ccf-mesh-dropdown"),
                                            dcc.Dropdown(
                                                options=[
                                                    {'label': region if region != 'root' else 'Brain',
                                                     'value': region}
                                                    for region in dataset.allen_ccf_regions
                                                ],
                                                id="ccf-mesh-dropdown",
                                                value=_default_ccf_mesh_selection(region_name),
                                                multi=True),
                                            dbc.FormText(
                                                dcc.Markdown(
                                                    "Load anatomical structures from "
                                                    "[the Allen CCFv3]"
                                                    "(http://atlas.brain-map.org/). "
                                                    "All the abbreviations are from "
                                                    "[the Allen Mouse Reference Atlas]"
                                                    "(http://atlas.brain-map.org/atlas?atlas=602630314)."
                                                )
                                            ),
                                            dbc.Label('Anatomical Structures Opacity',
                                                      html_for='ccf-mesh-opacity-slider',
                                                      className='mt-2'),
                                            dcc.Slider(
                                                id='ccf-mesh-opacity-slider',
                                                min=0.1,
                                                max=1,
                                                step=0.05,
                                                value=0.1,
                                                marks={i: str(i) for i in [0.1, 0.3, 0.5, 0.7, 0.9]}
                                            )
                                        ]
                                    )
                                ]
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, lg=3
            ),
            # 3D mesh
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Brain Dissection Regions & Anatomical Structures'),
                            dbc.CardBody(
                                [
                                    html.P(
                                        'Click legend to toggle structures. '
                                        'Note that tissues were dissected from both hemisphere.',
                                        className="text-muted"),
                                    dcc.Loading(
                                        [
                                            dcc.Graph(
                                                id='3d-mesh-graph',
                                                config={'displayModeBar': False}
                                            )
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
        ]
    )

    second_row = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.P(
                        [
                            'Cell Scatter Control (For more details, go to the ',
                            dbc.CardLink('Paired Scatter Browser', id='brain-region-pair-scatter-url'),
                            ')'
                        ],
                        className='mb-0'
                    )
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.FormGroup(
                                        [
                                            dbc.Label('Scatter Coords',
                                                      html_for='scatter-coords-dropdown',
                                                      className='mr-2'),
                                            dcc.Dropdown(
                                                options=[
                                                    {'label': name,
                                                     'value': name,
                                                     'disabled': False if (name in valid_coords) else True}
                                                    for name in dataset.coord_names],
                                                value='L1UMAP',
                                                id="scatter-coords-dropdown",
                                                clearable=False
                                            ),
                                            dbc.FormText(
                                                'Coordinates of both scatter plots.'
                                            )
                                        ],
                                        className='mr-3'
                                    )
                                ]
                            ),
                            dbc.Col(
                                [
                                    dbc.FormGroup(
                                        [
                                            dbc.Label('Region Level',
                                                      html_for='region-level-dropdown',
                                                      className='mr-2'),
                                            dcc.Dropdown(
                                                options=[
                                                    {'label': 'Dissection Region', 'value': 'RegionName'},
                                                    {'label': 'Sub-region', 'value': 'SubRegion'},
                                                    {'label': 'Major Region', 'value': 'MajorRegion'},
                                                ],
                                                value='RegionName',
                                                id="region-level-dropdown",
                                                clearable=False
                                            ),
                                            dbc.FormText('Color of the left scatter plot.')
                                        ],
                                        className='mr-3'
                                    )
                                ]
                            ),
                            dbc.Col(
                                [
                                    dbc.FormGroup(
                                        [
                                            dbc.Label('Cell Type Level',
                                                      html_for='cell-type-level-selector',
                                                      className='mr-2'),
                                            dcc.Dropdown(
                                                options=[
                                                    {'label': 'Cell Class', 'value': 'CellClass'},
                                                    {'label': 'Major Type', 'value': 'MajorType'},
                                                    {'label': 'Subtype', 'value': 'SubType'},
                                                ],
                                                value='MajorType',
                                                id="cell-type-level-selector",
                                                clearable=False
                                            ),
                                            dbc.FormText('Color of the middle scatter plots.')
                                        ],
                                        className='mr-3'
                                    )
                                ]
                            )
                        ],
                        form=True
                    )
                ]
            )
        ],
        className='my-3'
    )

    third_row = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Brain Region Scatter'),
                            dbc.Container(
                                [
                                    dcc.Graph(id='dissection-umap-graph')
                                ],
                                className='pt-3'
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, xl=4
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Cell Type Scatter'),
                            dbc.Container(
                                [
                                    dcc.Graph(id='cell-type-umap-graph')
                                ],
                                className='pt-3'
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, xl=4
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader('Cell Type Sunburst'),
                            dbc.CardBody(
                                [
                                    dcc.Graph(id='sunburst-graph'),
                                    html.A('Notes on cell type composition', className='text-muted',
                                           id='sunburst-notes'),
                                    dbc.Popover(
                                        [
                                            dbc.PopoverBody(
                                                SUNBURST_NOTES
                                            ),
                                        ],
                                        id="sunburst-notes-popover",
                                        is_open=False,
                                        target="sunburst-notes",
                                    ),
                                ]
                            )
                        ],
                        className='h-100'
                    )
                ],
                width=12, xl=4
            )
        ]
    )

    layout = html.Div(
        children=[
            # first row, info and anatomy
            first_row,
            # second row, UMAP control
            second_row,
            # third row, UMAP graphs
            third_row,
        ]
    )
    return layout


@app.callback(
    Output('3d-mesh-graph', 'figure'),
    [Input('ccf-mesh-dropdown', 'value'),
     Input('cemba-mesh-dropdown', 'value'),
     Input('ccf-mesh-opacity-slider', 'value')]
)
def make_3d_brain_mesh_figure(background_names, roi_names, background_opacity):
    data = []
    for region_name in sorted(background_names):
        data.append(_background_mesh(region_name, opacity=background_opacity))

    total_dissection_regions = []
    for region_name in sorted(roi_names):
        dissection_region_names = [dataset.region_label_to_cemba_name[i]
                                   for i in dataset.region_label_to_dissection_region_dict[region_name]]
        total_dissection_regions += dissection_region_names
    # dedup
    for region in set(total_dissection_regions):
        data.append(_roi_mesh(region))

    fig = go.Figure(data)

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=dict(
                eye=dict(  # this zoom in the initial view
                    x=0.9,
                    y=0.9,
                    z=0.9
                )
            )
        ),
        margin=dict(t=0, l=0, r=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


@lru_cache()
def _get_active_and_background_data(coord_name, region_name, region_level, cell_type_level, max_cells=7500):
    dissection_regions = dataset.region_label_to_dissection_region_dict[region_name]
    data = dataset.get_coords(coord_name)
    cell_meta = dataset.get_variables(list({'RegionName', region_level, cell_type_level})) \
        .reindex(data.index).astype(str)
    data = pd.concat([data, cell_meta], axis=1)

    active_data = data[data['RegionName'].isin(dissection_regions)]
    if active_data.shape[0] > max_cells:
        active_data = active_data.sample(max_cells, random_state=0)

    background_data = data[~data['RegionName'].isin(dissection_regions)]
    if background_data.shape[0] > max_cells:
        background_data = background_data.sample(max_cells, random_state=0)
    return active_data, background_data


def generate_scatter(active_data, background_data, hue, hover_name, hover_text):
    # selected_plot_df is colored and hover_data
    fig = px.scatter(active_data,
                     x="x",
                     y="y",
                     color=hue,
                     color_discrete_map=dataset.get_palette(hue),
                     hover_name=hover_name,
                     hover_data=[hover_text])
    fig.update_layout(showlegend=False,
                      margin=dict(t=30, l=0, r=30, b=0),
                      xaxis=go.layout.XAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      yaxis=go.layout.YAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    # update marker size and hover template
    fig.update_traces(mode='markers',
                      marker_size=n_cell_to_marker_size(active_data.shape[0]),
                      hovertemplate='<b>%{hovertext}</b><br>'
                                    f'<b>{hover_text}: </b>%{{customdata[0]}}<br>')

    # unselected_plot_df is gray background, no hover
    if background_data.shape[0] > 10:
        fig.add_trace(
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
    fig.data = fig.data[::-1]
    return fig


@app.callback(
    Output('dissection-umap-graph', 'figure'),
    [Input('scatter-coords-dropdown', 'value'),
     Input('region-level-dropdown', 'value')],
    [State('region-name', 'children'),
     State('cell-type-level-selector', 'value')]
)
def update_region_umap_figure(coord_name, region_level, region_name, cell_type_level):
    active_data, background_data = _get_active_and_background_data(
        coord_name=coord_name,
        region_name=region_name,
        region_level=region_level,
        cell_type_level=cell_type_level)

    fig = generate_scatter(
        active_data,
        background_data,
        hue=region_level,
        hover_name=region_level,
        hover_text=cell_type_level)
    return fig


@app.callback(
    Output('cell-type-umap-graph', 'figure'),
    [Input('scatter-coords-dropdown', 'value'),
     Input('cell-type-level-selector', 'value')],
    [State('region-name', 'children'),
     State('region-level-dropdown', 'value')]
)
def update_cell_type_umap_figure(coord_name, cell_type_level, region_name, region_level):
    active_data, background_data = _get_active_and_background_data(
        coord_name=coord_name,
        region_name=region_name,
        region_level=region_level,
        cell_type_level=cell_type_level)

    fig = generate_scatter(
        active_data,
        background_data,
        hue=cell_type_level,
        hover_name=cell_type_level,
        hover_text=region_level)
    return fig


@app.callback(
    Output('sunburst-graph', 'figure'),
    [Input('region-name', 'children')]
)
def update_cell_type_sunburst(region_name):
    dissection_regions = dataset.region_label_to_dissection_region_dict[region_name]
    region_judge = dataset.get_variables('RegionName').isin(dissection_regions)
    active_cells = region_judge[region_judge].index

    levels = CELL_TYPE_LEVELS
    fig = create_sunburst(
        levels=levels,
        selected_cells=active_cells
    )
    return fig


@app.callback(
    Output('brain-region-pair-scatter-url', 'href'),
    [Input('scatter-coords-dropdown', 'value'),
     Input('cell-type-level-selector', 'value'),
     Input('region-name', 'children')]
)
def make_pair_scatter_markdown(coords, cell_type_level, region_name):
    url = f'/{APP_ROOT_NAME}scatter?coords={coords};meta={cell_type_level};br={region_name}'.replace(' ', '%20')
    return url


@app.callback(
    Output("sunburst-notes-popover", "is_open"),
    [Input("sunburst-notes", "n_clicks")],
    [State("sunburst-notes-popover", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open
