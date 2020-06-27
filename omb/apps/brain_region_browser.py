import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from .default_values import *
from ..app import app

CELL_TYPE_LEVELS = ['CellClass', 'MajorType', 'SubType']
REGION_LEVELS = ['MajorRegion', 'SubRegion', 'Region']
DEFAULT_BRAIN_REGION_IMG_TITLE = 'Click a cell on the left to display its dissection region'
DEFAULT_BRAIN_REGION_IMG_SRC = '/assets/dissection_region_img/brain_region_demo.jpg'
DOWN_SAMPLE = 10000

region_browser_app = dash.Dash(__name__)

region_browser_app.layout = html.Div(children=[
    # store for selected regions
    dcc.Store(id='selected_brain_regions'),

    # first column, for control panel
    html.Div(children=[
        html.Div(
            children=[
                html.H6('Selected Data', className='control_label'),
                # basic numbers
                html.Div([
                    html.Div(
                        [html.H6(id="region_browser_n_cells", children='0'), html.P("Nuclei")],
                        className="mini_container six columns",
                    ),
                    html.Div(
                        [html.H6(id="region_browser_n_regions", children='0'), html.P("Dissection Region")],
                        className="mini_container six columns",
                    )
                ], className='row container-display')],
            className='pretty_container'),

        # control components
        html.Div([
            html.H6(children='Select Regions', className='control_label'),
            html.P('(Showing the union of selected labels)', className="control_label"),
            dcc.Dropdown(
                options=[{'label': region, 'value': region}
                         for region in dataset.region_label_to_dissection_region_dict.keys()],
                id="region_selector",
                value=['ALL REGIONS'],
                multi=True,
                placeholder='Showing all regions',
                className="dcc_control",
            )], className="mini_container"),
        html.Div([
            html.H6("Select Coordinates", className="control_label"),
            dcc.Dropdown(
                options=[{'label': name, 'value': name}
                         for name in dataset.coord_names],
                value='L1UMAP',
                id="coord_selector",
                clearable=False,
                className="dcc_control"
            ),
            dcc.ConfirmDialog(
                id='no_cell_warning',
                message='No cells from current selected regions appear in this coordinate set, '
                        'the plot will not update.',
            ),
        ], className="mini_container"),
        html.Div([
            html.H6(children='Select Color', className='control_label'),
            html.P("Region Level", className="control_label"),
            dcc.Dropdown(
                options=[
                    {'label': 'Dissection Region', 'value': 'Region'},
                    {'label': 'Sub-Region', 'value': 'SubRegion'},
                    {'label': 'Major Region', 'value': 'MajorRegion'},
                ],
                value='SubRegion',
                id="region_level_selector",
                clearable=False,
                className="dcc_control"),
            html.P("Cell Type Level", className="control_label"),
            dcc.Dropdown(
                options=[
                    {'label': 'Cell Class', 'value': 'CellClass'},
                    {'label': 'Major Type', 'value': 'MajorType'},
                    {'label': 'Subtype', 'value': 'SubType'},
                ],
                value='MajorType',
                id="cell_type_level_selector",
                clearable=False,
                className="dcc_control"
            )], className="mini_container"),
        html.Button('Update Graphs', id='update_button', n_clicks=0,
                    className='offset-by-two columns eight columns'),
    ], id='control_panel', className='pretty_container three columns'),

    # second column, for all data panels
    html.Div(children=[
        # first row is for region plots
        html.Div(
            children=[
                html.Div(
                    children=[dcc.Graph(id='region_scatter')],
                    className='six columns pretty_container',
                    style={'margin': '2px',
                           'padding': '2px'}),
                html.Div(
                    children=[
                        html.H6(DEFAULT_BRAIN_REGION_IMG_TITLE,
                                id='brain_region_img_title'),
                        html.Img(
                            id='brain_region_img',
                            src=DEFAULT_BRAIN_REGION_IMG_SRC,
                            style={
                                "max-width": "100%",
                                "height": "auto"
                            })],
                    className='six columns pretty_container',
                    style={'margin': '2px',
                           'padding': '2px'})],
            id='region_row',
            className='row container-display',
            style={'margin': '2px',
                   'padding': '2px'}),

        # second row is for cell type plots
        html.Div(
            children=[
                html.Div(
                    children=[dcc.Graph(id='cell_type_scatter')],
                    className='six columns pretty_container',
                    style={'margin': '2px',
                           'padding': '2px'}),
                html.Div(
                    children=[dcc.Graph(id='cell_type_sunburst')],
                    className='six columns pretty_container',
                    style={'margin': '2px',
                           'padding': '2px'})],
            id='cell_type_row',
            className='row container-display',
            style={'margin': '2px',
                   'padding': '2px'}),

        # third row is for cell type barplot
        html.Div(
            children=[

            ],
            id='cell_type_bar_row',
            className='row pretty_container container-display'),

        # fourth row is for cell type table
        html.Div(
            children=[

            ],
            id='cell_type_table_row',
            className='row pretty_container container-display'),
    ], id='data_panel', className='nine columns')
], id='region_browser_div')


def get_split_plot_df(coord_base, variable_name, selected_regions, hover_cols=('RegionName', 'SubType')):
    hue_palette = dataset.get_palette(variable_name)
    plot_df = dataset.get_coords(coord_base)

    cell_region_names = dataset.get_variables('RegionName')
    selected_cell_ids = cell_region_names[cell_region_names.isin(selected_regions)].index

    # some coords do not have all cell so selected index need to be updated
    selected_cell_index = selected_cell_ids & plot_df.index
    if len(selected_cell_index) == 0:
        raise PreventUpdate
    unselected_cell_index = plot_df.index[~plot_df.index.isin(selected_cell_index)]

    hover_cols = list(hover_cols)
    # add hover data and color data
    if variable_name not in hover_cols:
        hover_cols.append(variable_name)
    for col_name in hover_cols:
        plot_df[col_name] = dataset.get_variables(col_name).astype(str)

    # selected
    selected_plot_df = plot_df.loc[selected_cell_index]
    unselected_plot_df = plot_df.loc[unselected_cell_index]
    return selected_plot_df, unselected_plot_df, hover_cols, hue_palette


def n_cell_to_marker_size(n_cells):
    if n_cells > 20000:
        size = 1
    elif n_cells > 10000:
        size = 2
    elif n_cells > 5000:
        size = 3
    elif n_cells > 1000:
        size = 4
    elif n_cells > 500:
        size = 5
    elif n_cells > 100:
        size = 6
    elif n_cells > 50:
        size = 7
    elif n_cells > 10:
        size = 8
    else:
        size = 9
    return size


def generate_scatter(selected_plot_df, unselected_plot_df, hue, palette, hover_name, hover_cols):
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

    # unselected_plot_df is gray background, no hover
    if unselected_plot_df.shape[0] > 100:
        fig.add_trace(
            go.Scattergl(
                x=unselected_plot_df['x'],
                y=unselected_plot_df['y'],
                mode='markers',
                marker_size=n_cell_to_marker_size(unselected_plot_df.shape[0]) - 1,
                marker_color='rgba(200, 200, 200, .5)',
                hoverinfo='skip')
        )
    # reorder data to put the background trace in first (bottom)
    fig.data = fig.data[::-1]
    return fig


def region_selector_to_region_list(input_list):
    total_selected_regions = []
    region_to_dissect_region_map = dataset.region_label_to_dissection_region_dict
    for region in input_list:
        total_selected_regions += region_to_dissect_region_map[region]
    region_selected = list(set(total_selected_regions))
    return region_selected


@app.callback([Output('selected_brain_regions', 'data'),
               Output('region_browser_n_cells', 'children'),
               Output('region_browser_n_regions', 'children')],
              [Input('region_selector', 'value')])
def update_selected_regions(region_selected):
    # use all the regions on initial load/no region selected.
    if (region_selected is None) or (len(region_selected) == 0):
        region_selected = dataset.dissection_regions
    else:
        region_selected = region_selector_to_region_list(region_selected)

    # n regions
    n_regions = len(region_selected)

    # update data
    data = {'regions': region_selected}

    # n cells
    region_cell_counts = dataset.get_variables('RegionName').value_counts()
    n_cells = sum([region_cell_counts[r] for r in region_selected])

    return data, n_cells, n_regions


@app.callback(Output('region_scatter', 'figure'),
              [Input('update_button', 'n_clicks')],
              [State('coord_selector', 'value'),
               State('region_level_selector', 'value'),
               State('selected_brain_regions', 'data')])
def update_region_scatter(n_clicks, coord_base, region_level, data):
    if data is None:
        # this is the initial fire where data haven't been initiated
        # showing all regions by default
        data = {'regions': dataset.dissection_regions}

    selected_plot_df, unselected_plot_df, hover_cols, palette = get_split_plot_df(
        coord_base=coord_base,
        variable_name=region_level,
        selected_regions=data['regions'],
        hover_cols=('RegionName', 'SubType'))

    if selected_plot_df.shape[0] > DOWN_SAMPLE:
        selected_plot_df = selected_plot_df.sample(DOWN_SAMPLE, random_state=0)
    if unselected_plot_df.shape[0] > DOWN_SAMPLE:
        unselected_plot_df = unselected_plot_df.sample(DOWN_SAMPLE, random_state=0)

    # make figure
    fig = generate_scatter(
        selected_plot_df,
        unselected_plot_df,
        hue=region_level,
        palette=palette,
        hover_name=region_level,
        hover_cols=hover_cols)
    return fig


@app.callback(
    Output('no_cell_warning', 'displayed'),
    [Input('coord_selector', 'value'),
     Input('region_selector', 'value')]
)
def validate_coord_base_and_region_selection(coord_base, region_selected):
    if (region_selected == []) or (region_selected is None):
        region_selected = ['ALL REGIONS']
    cell_dissection_region = dataset.get_variables('RegionName')
    region_selected = region_selector_to_region_list(region_selected)

    selected_cells = cell_dissection_region[cell_dissection_region.isin(region_selected)].index
    coord_df = dataset.get_coords(coord_base)
    if (coord_df.index & selected_cells).size == 0:
        return True
    else:
        return False


@app.callback(Output('cell_type_scatter', 'figure'),
              [Input('update_button', 'n_clicks')],
              [State('coord_selector', 'value'),
               State('cell_type_level_selector', 'value'),
               State('selected_brain_regions', 'data')])
def update_cell_type_scatter(n_clicks, coord_base, cell_type_level, data):
    print(n_clicks, 'update_cell_type_scatter')
    if data is None:
        # this is the initial fire where data haven't been initiated
        # showing all regions by default
        data = {'regions': dataset.dissection_regions}

    selected_plot_df, unselected_plot_df, hover_cols, palette = get_split_plot_df(
        coord_base=coord_base,
        variable_name=cell_type_level,
        selected_regions=data['regions'],
        hover_cols=('RegionName', 'SubType'))

    if selected_plot_df.shape[0] > DOWN_SAMPLE:
        selected_plot_df = selected_plot_df.sample(DOWN_SAMPLE, random_state=0)
    if unselected_plot_df.shape[0] > DOWN_SAMPLE:
        unselected_plot_df = unselected_plot_df.sample(DOWN_SAMPLE, random_state=0)

    # make figure
    fig = generate_scatter(
        selected_plot_df,
        unselected_plot_df,
        hue=cell_type_level,
        palette=palette,
        hover_name=cell_type_level,
        hover_cols=hover_cols)
    return fig


def create_sunburst(levels, selected_cells):
    data = dataset.get_variables(levels).loc[selected_cells]
    if 'SubType' in levels:
        data = data[data['SubType'].apply(lambda c: 'Outlier' not in c)]

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
    fig.update_layout(margin=dict(t=15, l=0, r=0, b=15),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    return fig


@app.callback(
    Output('cell_type_sunburst', 'figure'),
    [Input('update_button', 'n_clicks')],
    [State('selected_brain_regions', 'data')]
)
def update_cell_type_sunburst(n_clicks, data):
    if data is not None:
        # this is the initial fire where data haven't been initiated
        # showing all regions by default
        selected_regions = data['regions']
    else:
        selected_regions = dataset.dissection_regions

    cell_region_names = dataset.get_variables('RegionName')
    selected_cells = cell_region_names.index[cell_region_names.isin(selected_regions)]

    levels = CELL_TYPE_LEVELS
    fig = create_sunburst(
        levels=levels,
        selected_cells=selected_cells
    )
    return fig


@app.callback(
    [Output('brain_region_img_title', 'children'),
     Output('brain_region_img', 'src')],
    [Input('region_scatter', 'clickData'),
     Input('update_button', 'n_clicks')]
)
def update_brain_region_img(clicked_cell_id, n_clicks):
    # if the update_button triggered this callback, reset the img
    try:
        if dash.callback_context.triggered[0]['prop_id'] == 'update_button.n_clicks':
            return DEFAULT_BRAIN_REGION_IMG_TITLE, DEFAULT_BRAIN_REGION_IMG_SRC
    except TypeError:
        # init trigger where this no clicked data
        return DEFAULT_BRAIN_REGION_IMG_TITLE, DEFAULT_BRAIN_REGION_IMG_SRC
        
    # example input from clickData
    # {'points': [{'curveNumber': 5,
    #              'pointNumber': 246,
    #              'pointIndex': 246,
    #              'x': -7.69921875,
    #              'y': -29.4375,
    #              'hovertext': 'MOp',
    #              'customdata': ['MOp-3', 'IT-L5 Grik3', 'MOp']}]}
    # print('click', clicked_cell_id)

    # this is always dissection region unless the above code changed.
    dissection_region, subtype = clicked_cell_id['points'][0]['customdata'][:2]

    cell_class = dataset.sub_type_to_cell_class[subtype]
    major_region = dataset.dissection_region_to_major_region[dissection_region]

    title = f'A "{subtype}" ({cell_class}) cell from {dissection_region} ({major_region})'
    src = f'/assets/dissection_region_img/{dissection_region}.jpeg'

    return title, src
