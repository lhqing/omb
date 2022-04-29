import dash_bootstrap_components as dbc
import dash_core_components as dcc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.cluster import MiniBatchKMeans
from sklearn.impute import SimpleImputer

from .default_values import *
from ..app import app

DMR_LENGTH_BINS = (0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 99999999999)
DMS_BINS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 99999999999)


def _bin_to_labels(bins):
    new_bins = list(bins[:-1]) + ['inf']
    return [f'({new_bins[i]}, {new_bins[i + 1]}]'
            for i in range(len(new_bins) - 1)]


def _get_dmr_bar_plots(selected_dmr):
    length = dataset.dmr_ds['end'] - dataset.dmr_ds['start']
    dmr_length = length.to_pandas()
    dmr_length_dist_total = pd.cut(
        dmr_length,
        bins=DMR_LENGTH_BINS
    ).value_counts().sort_index() / dmr_length.size * 100
    dmr_length_dist_selected = pd.cut(
        dmr_length.loc[selected_dmr],
        bins=DMR_LENGTH_BINS
    ).value_counts().sort_index() / selected_dmr.size * 100

    dms = dataset.dmr_ds['number_of_dms'].to_pandas()
    dms_dist_total = pd.cut(
        dms,
        bins=DMS_BINS
    ).value_counts().sort_index() / dmr_length.size * 100
    dms_dist_selected = pd.cut(
        dms.loc[selected_dmr],
        bins=DMS_BINS
    ).value_counts().sort_index() / selected_dmr.size * 100

    fig = make_subplots(rows=1, cols=2)

    fig.add_trace(go.Bar(name='Total',
                         legendgroup='Total',
                         x=list(range(len(DMR_LENGTH_BINS))),
                         y=dmr_length_dist_total.values,
                         marker_color='gray'),
                  row=1,
                  col=1)
    fig.add_trace(go.Bar(name='Selected DMRs',
                         legendgroup='Selected DMRs',
                         x=list(range(len(DMR_LENGTH_BINS))),
                         y=dmr_length_dist_selected.values,
                         marker_color='salmon'),
                  row=1,
                  col=1)
    fig.add_trace(go.Bar(name='Total',
                         legendgroup='Total',
                         showlegend=False,
                         x=list(range(len(DMS_BINS))),
                         y=dms_dist_total.values,
                         marker_color='gray'),
                  row=1,
                  col=2)
    fig.add_trace(go.Bar(name='Selected DMRs',
                         legendgroup='Selected DMRs',
                         showlegend=False,
                         x=list(range(len(DMS_BINS))),
                         y=dms_dist_selected.values,
                         marker_color='salmon'),
                  row=1,
                  col=2)
    fig.update_yaxes(title='% of DMRs')

    fig.update_xaxes(tickvals=list(range(len(DMR_LENGTH_BINS))),
                     ticktext=_bin_to_labels(DMR_LENGTH_BINS),
                     title='DMR Length (bp)',
                     row=1, col=1)

    fig.update_xaxes(tickvals=list(range(len(DMS_BINS))),
                     ticktext=_bin_to_labels(DMS_BINS),
                     title='Number of DMS',
                     row=1, col=2)

    fig.update_layout(barmode='group')
    fig.update_traces(hovertemplate='%{y:.2f}% of')
    return fig


def _ordered_ave_dmr_df(data, row_k=10, max_rows=500):
    if data.shape[0] > max_rows:
        # further ave to make plots, only ~500 rows will remain
        ave = data.groupby(data.index // (data.shape[0] // 500 + 1)).mean()
    else:
        ave = data
    # fill NA, if any
    ave = pd.DataFrame(SimpleImputer().fit_transform(ave), columns=ave.columns)

    # row order by kmeans
    row_cluster = MiniBatchKMeans(n_clusters=row_k,
                                  random_state=0,
                                  batch_size=6)
    row_cluster.fit(ave)
    row_order = np.argsort(row_cluster.labels_)

    # col order by ward clustering
    col_linkage = linkage(ave.T, method='ward')
    col_dendrogram = dendrogram(col_linkage, no_plot=True)
    col_order = list(map(int, col_dendrogram['ivl']))

    ordered_ave = ave.iloc[row_order, col_order].copy().reset_index(drop=True)
    return ordered_ave


def _get_dmr_bar_heatmap(dmr_df, row_k, max_rows, color_type):
    plot_data = _ordered_ave_dmr_df(dmr_df, row_k=row_k, max_rows=max_rows)

    fig = make_subplots(rows=2, cols=1,
                        row_heights=[0.3, 0.7],
                        shared_xaxes=True,
                        vertical_spacing=0.05)
    if color_type == 'mCGFrac':
        bar_ylabel = 'mCG / CG Frac.'
    elif color_type == 'REPTILE':
        bar_ylabel = 'REPTILE Score'
    else:
        bar_ylabel = ''

    # Subtype barplot
    palette = dataset.get_palette('SubType')
    for cluster, data in plot_data.items():
        fig.add_trace(
            go.Box(
                y=data,
                boxpoints=False,
                orientation='v',
                name=cluster,
                marker_color=palette[cluster.replace('_', ' ')]
            ),
            row=1,
            col=1)
    fig.update_yaxes(title=bar_ylabel, row=1, col=1)

    # DMR by Subtype heatmap
    fig.add_trace(
        go.Heatmap(
            z=plot_data.values,
            x=plot_data.columns,
            y=plot_data.index
        ),
        row=2,
        col=1)
    fig.update_yaxes(showline=False,
                     zeroline=False,
                     showgrid=False,
                     showticklabels=False,
                     ticks=None, row=2, col=1)
    fig.update_traces(hovertemplate='<b>Subtype: </b>%{x}<br>'
                                    '<b>mCG/CG: </b>%{z:.2f}'
                                    '<extra></extra>', row=2, col=1)
    fig.update_yaxes(title='Selected DMRs',
                     showline=False,
                     zeroline=False,
                     showgrid=False,
                     showticklabels=False,
                     ticks=None,
                     row=2,
                     col=1)

    fig.update_layout(showlegend=False,
                      margin=dict(t=0, l=0, r=0, b=0))
    return fig


def create_cell_type_dmr_layout():
    coi_forms = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Cell type Of Interest (COI)'),
                    dcc.Dropdown(id='coi-dropdown',
                                 options=[{'label': c.replace('_', ' '), 'value': c}
                                          for c in sorted(dataset.dmr_subtype)],
                                 multi=True,
                                 value=['MGE-Sst_Chodl'],
                                 clearable=True),
                    dbc.FormText('Finding hypo-DMRs from these cell types.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Logic Type', size='sm'),
                    dbc.Input('coi-logic-input', value='any',
                              placeholder="Input 'any', 'all' or an integer."),
                    dbc.FormFeedback("Only accept 'any', 'all', or an integer between 1 to len(COI).", valid=False),
                    dbc.FormText('Include DMRs having hypo-methylation in __ of the cell types selected above.'),
                ]
            )
        ]
    )
    cte_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Cell type to exclude'),
                    dcc.Dropdown(id='cte-dropdown',
                                 options=[{'label': c.replace('_', ' '), 'value': c}
                                          for c in sorted(dataset.dmr_subtype)],
                                 multi=True,
                                 value=[],
                                 clearable=True),
                    dbc.FormText('Excluding hypo-DMRs from these cell types.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Logic Type', size='sm'),
                    dbc.Input('cte-logic-input', value='all',
                              placeholder="Input 'any', 'all' or an integer."),
                    dbc.FormFeedback("Only accept 'any', 'all', or an integer between 1 to len(CTE).", valid=False),
                    dbc.FormText('Exclude DMRs having hypo-methylation in __ of the cell types selected above.')

                ]
            )
        ]
    )
    heatmap_color_form = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Heatmap Color',
                              html_for='color-dropdown'),
                    dcc.Dropdown(id='color-dropdown',
                                 options=[
                                     {'label': 'mCG/CG Fraction', 'value': 'mCGFrac'},
                                     {'label': 'REPTILE Score', 'value': 'REPTILE'}
                                 ],
                                 clearable=False,
                                 multi=False,
                                 value='mCGFrac'),
                    dbc.FormText('DMR heatmap hue type.')
                ]
            )
        ]
    )
    cutoff_forms = dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Number of DMS >=', html_for='dms-input'),
                    dbc.Input(type="number", min=0, max=10, step=1, value=2, id='dms-input'),
                    dbc.FormText('Filter DMRs by the number of differentially methylated CpG pairs.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('Effect size >', html_for='effect-size-slider'),
                    dcc.Slider(id='effect-size-slider', min=0.1, max=0.9, step=0.05, value=0.4,
                               marks={i: str(i) for i in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]}),
                    dbc.FormText('mCG/CG difference between COI and robust mean of all subtypes.')
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label('REPTILE score >', html_for='reptile-slider'),
                    dcc.Slider(id='reptile-slider', min=0.1, max=0.9, step=0.05, value=0.7,
                               marks={i: str(i) for i in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]}),
                    dbc.FormText('REPTILE score of COI.')
                ]
            )
        ]
    )
    layout = html.Div(
        [
            # store of selected DMRs
            dcc.Store(id='selected-dmr-store',
                      data={'selected_dmr': []}),

            # first row is DMR basic info and control
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Jumbotron(
                                [
                                    html.H4('Cell Type Specific DMRs')
                                ],
                                className='h-100'
                            )
                        ],
                        width=12, md=12, xl=3
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader('Cell Type Selection'),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            coi_forms
                                                        ]
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            cte_form
                                                        ]
                                                    )
                                                ]
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            heatmap_color_form
                                                        ]
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button('Update All Stats',
                                                                       id='update-btn',
                                                                       color='success'),
                                                            html.P('Can take up to 1 minute.',
                                                                   className='text-muted',
                                                                   style={'font-size': '0.8rem'})
                                                        ],
                                                        className='m-auto'
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                className='h-100'
                            )
                        ],
                        width=12, md=8, xl=5
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader('DMR Filters'),
                                    dbc.CardBody(
                                        [
                                            cutoff_forms
                                        ]
                                    )
                                ],
                                className='h-100'
                            )
                        ],
                        width=12, md=6, xl=4
                    )
                ],
                className='my-3'
            ),


            dbc.Row(
                [
                    # second row is dist plots
                    dbc.Row(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader('DMR Information Bar Plots'),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(id='dmr-bar')
                                        ],
                                        className='m-0'
                                    )
                                ],
                                className='w-100'
                            )
                        ],
                        className='my-3 w-100'
                    ),

                    # third row is the heatmap
                    dbc.Row(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader('DMR by Subtype Heatmap'),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id='dmr-heatmap',
                                                style={"height": "80vh", "width": "auto"}
                                            )
                                        ]
                                    )
                                ],
                                className='w-100'
                            )
                        ],
                        className='my-3 w-100'
                    )
                ]
            )
        ]
    )
    return layout


@app.callback(
    [Output('cte-dropdown', 'value'),
     Output('cte-dropdown', 'options')],
    [Input('coi-dropdown', 'value')],
    [State('cte-dropdown', 'value')]
)
def update_cte_dropdown(coi, cte):
    if coi is None or len(coi) == 0:
        raise PreventUpdate
    coi = set(coi)
    new_cte = [i for i in cte if i not in coi]
    new_cte_options = [{'label': c, 'value': c, 'disabled': c in coi} for c in sorted(dataset.dmr_subtype)]
    return new_cte, new_cte_options


def _valid_logic_and_options(logic, options):
    if logic:
        if logic in {'all', 'any'}:
            return True, False
        else:
            try:
                coi_logic = int(logic)
                if 0 < coi_logic <= len(options):
                    return True, False
                else:
                    return False, True
            except ValueError:
                return False, True
    return False, False


@app.callback(
    [Output("coi-logic-input", "valid"), Output("coi-logic-input", "invalid")],
    [Input("coi-logic-input", "value")],
    [State('coi-dropdown', 'value')]
)
def check_validity(coi_logic, coi):
    return _valid_logic_and_options(coi_logic, coi)


@app.callback(
    [Output("cte-logic-input", "valid"), Output("cte-logic-input", "invalid")],
    [Input("cte-logic-input", "value")],
    [State('cte-dropdown', 'value')]
)
def check_validity(cte_logic, cte):
    return _valid_logic_and_options(cte_logic, cte)


def _valid_logic(logic):
    if logic in {'all', 'any'}:
        return True
    try:
        int(logic)
        return True
    except ValueError:
        return False


@app.callback(
    Output('selected-dmr-store', 'data'),
    [Input('update-btn', 'n_clicks')],
    [State('coi-dropdown', 'value'),
     State('coi-logic-input', 'value'),
     State('cte-dropdown', 'value'),
     State('cte-logic-input', 'value'),
     State('dms-input', 'value'),
     State('effect-size-slider', 'value'),
     State('reptile-slider', 'value'),
     State('color-dropdown', 'value')],
    prevent_initial_call=True
)
def select_dmr(_,
               coi,
               coi_logic,
               cte,
               cte_logic,
               dms_cutoff,
               effect_size_cutoff,
               reptile_cutoff,
               color_type):
    if (coi is None) or (len(coi) == 0) or (not _valid_logic(coi_logic)) or (not _valid_logic(cte_logic)):
        raise PreventUpdate

    selected_dmr = dataset.query_dmr(cluster_of_interest=tuple(coi) if isinstance(coi, list) else coi,
                                     coi_logic=coi_logic,
                                     cluster_to_exclude=tuple(cte) if isinstance(cte, list) else cte,
                                     cte_logic=cte_logic,
                                     number_of_dms=dms_cutoff,
                                     reptile_cutoff=reptile_cutoff,
                                     delta_to_robust_mean=effect_size_cutoff)
    return {'selected_dmr': selected_dmr}


@app.callback(
    [Output('dmr-bar', 'figure'),
     Output('dmr-heatmap', 'figure')],
    [Input('selected-dmr-store', 'data'),
     Input('color-dropdown', 'value')],
    prevent_initial_call=True
)
def get_figures(data, color_type):
    selected_dmr = pd.Index(data['selected_dmr'])
    # final data for plots
    dmr_frac_df = dataset.dmr_ds[color_type].sel({'id': selected_dmr}).to_pandas().reset_index(drop=True)
    fig_bar = _get_dmr_bar_plots(selected_dmr)
    fig_heatmap = _get_dmr_bar_heatmap(dmr_frac_df,
                                       row_k=10,
                                       max_rows=500,
                                       color_type=color_type)
    return fig_bar, fig_heatmap
