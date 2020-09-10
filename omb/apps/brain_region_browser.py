from functools import lru_cache

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

from .default_values import *
from .sunburst import create_sunburst
from .utilities import n_cell_to_marker_size
from ..app import app


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
**Description**: {n_cells} cells from {n_region} dissection region{"s" if n_region != 1 else ""}.

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

    include_regions = ['root'] + this_region_table['Major Region'].unique().tolist()  # always add the whole brain
    return include_regions


def create_brain_region_browser_layout(region_name):
    region_name = region_name.replace('%20', ' ')
    valid_coords = _get_valid_coords(region_name)
    if region_name not in dataset.region_label_to_dissection_region_dict:
        return None

    layout = html.Div(children=[
        # first row, info and anatomy
        html.Div(children=[
            # brain region info
            html.Div(
                children=[
                    html.H1(region_name, id='region-name'),
                    dcc.Markdown(children=_brain_region_info_markdown(region_name))
                ],
                className='pretty_container two columns'),

            # anatomy 3d control
            html.Div([
                html.Div(
                    html.H5('3D Mesh Control')
                ),
                html.Br(),
                html.H6(children='Anatomical Structures'),
                dcc.Markdown('Load any anatomical structures from [the Allen CCFv3](http://atlas.brain-map.org/).'),
                dcc.Dropdown(
                    options=[{'label': region if region != 'root' else 'Brain', 'value': region}
                             for region in dataset.allen_ccf_regions],
                    id="ccf-mesh-dropdown",
                    value=_default_ccf_mesh_selection(region_name),
                    multi=True),
                html.Br(),
                html.P('CCF mesh opacity: '),
                dcc.Slider(
                    id='ccf-mesh-opacity-slider',
                    min=0.1,
                    max=1,
                    step=0.05,
                    value=0.1,
                    marks={i: str(i) for i in [0.1, 0.3, 0.5, 0.7, 0.9]}
                ),
                html.Br(),
                html.H6('Dissection Regions'),
                dcc.Dropdown(
                    options=[{'label': region, 'value': region}
                             for region in dataset.region_label_to_dissection_region_dict.keys()],
                    id="cemba-mesh-dropdown",
                    value=[region_name],
                    multi=True),
            ], className="pretty_container three columns"),

            # 3-D mesh graph
            html.Div(
                children=[
                    html.H5('Brain Dissection Region & Anatomical Structures'),
                    html.P('Click legend to toggle structures. '
                           'Note that tissues were dissected from both hemisphere.'),
                    dcc.Loading(children=[dcc.Graph(id='3d-mesh-graph',
                                                    config={'displayModeBar': False})],
                                type='circle')
                ],
                className='pretty_container seven columns'
            )
        ], className='row container-display'),

        # second row, UMAP control
        html.Div(
            children=[
                html.Div(
                    [html.H5('UMAP Control'),
                     dcc.Markdown(id='brain-region-pair-scatter-markdown')],
                    className='two columns'
                ),
                html.Div(
                    children=[
                        html.H6('Scatter Coords'),
                        dcc.Dropdown(
                            options=[{'label': name, 'value': name,
                                      'disabled': False if (name in valid_coords) else True}
                                     for name in dataset.coord_names],
                            value='L1UMAP',
                            id="scatter-coords-dropdown",
                            clearable=False,
                            className="dcc_control"
                        )
                    ], className='four columns'
                ),
                html.Div(
                    children=[
                        html.H6('Region Level'),
                        dcc.Dropdown(
                            options=[
                                {'label': 'Dissection Region', 'value': 'RegionName'},
                                {'label': 'Sub-Region', 'value': 'SubRegion'},
                                {'label': 'Major Region', 'value': 'MajorRegion'},
                            ],
                            value='RegionName',
                            id="region-level-dropdown",
                            clearable=False,
                            className="dcc_control")
                    ], className='four columns'
                ),
                html.Div(
                    children=[
                        html.H6('Cell Type Level'),
                        dcc.Dropdown(
                            options=[
                                {'label': 'Cell Class', 'value': 'CellClass'},
                                {'label': 'Major Type', 'value': 'MajorType'},
                                {'label': 'Subtype', 'value': 'SubType'},
                            ],
                            value='MajorType',
                            id="cell-type-level-selector",
                            clearable=False,
                            className="dcc_control"
                        )
                    ], className='four columns'
                ),
            ],
            className='pretty_container row container-display'
        ),

        # third row, UMAP graphs
        html.Div(
            children=[
                html.Div(
                    [html.H5('UMAP Color By Dissection Region'),
                     dcc.Graph(id='dissection-umap-graph')],
                    className='pretty_container four columns'
                ),
                html.Div(
                    [html.H5('UMAP Color By Cell Type'),
                     dcc.Graph(id='cell-type-umap-graph')],
                    className='pretty_container four columns'
                ),
                html.Div(
                    [html.H5('Cell Type Sunburst'),
                     dcc.Graph(id='sunburst-graph')],
                    className='pretty_container four columns'
                ),
            ],
            className='row container-display'
        )
    ])
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
                      margin=dict(t=15, l=0, r=0, b=15),
                      xaxis=go.layout.XAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      yaxis=go.layout.YAxis(title='', showticklabels=False, showgrid=False, zeroline=False),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')

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
    Output('brain-region-pair-scatter-markdown', 'children'),
    [Input('scatter-coords-dropdown', 'value'),
     Input('cell-type-level-selector', 'value'),
     Input('region-name', 'children')]
)
def make_pair_scatter_markdown(coords, cell_type_level, region_name):
    url = f'/scatter?coords={coords};meta={cell_type_level};br={region_name}'
    text = f'For more details, go to the [**Paired Scatter Browser**]({url})'
    return text
