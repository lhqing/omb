import dash_core_components as dcc
import dash_html_components as html
import dash_table


def create_cell_type_browser_layout(cell_type_name):
    layout = html.Div(children=[
        # first row is cell_type_card and region_compo_sunburst
        html.Div(
            children=[
                html.Div(children=[
                    html.H3(children=cell_type_name,
                            id='cell_type_browser_title',
                            style={"margin-right": "20px"}),
                    html.P(children='N_CELL Nuclei', id='cell_type_browser_cell_number'),
                    html.P(children='Parents', id='parents'),
                    html.P(children='Siblings', id='siblings'),
                    html.P(children='Description', id='description'),
                ], className='pretty_container three columns'),
                html.Div(children=[
                    html.P('Mapping Metric Violin Plot'),
                    dcc.Graph(id='metric_violin')
                ], className='pretty_container three columns'),
                html.Div(children=[
                    html.P('Brain Region Barplot'),
                    dcc.Graph(id='region_bar_plot')
                ], className='pretty_container two columns'),
                html.Div(children=[
                    html.P('Brain Region Sunburst'),
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

                    ],
                    id='scatter_control',
                    className='pretty_container two columns'),
                html.Div(
                    children=[
                        html.P('Scatter Plot - Cell Type'),
                        dcc.Graph(id='scatter_plot_1')
                    ],
                    className='pretty_container five columns'
                ),
                html.Div(
                    children=[
                        html.P('Scatter Plot - Gene'),
                        dcc.Graph(id='scatter_plot_2')
                    ],
                    className='pretty_container five columns'
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