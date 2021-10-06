import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from .cell_type_browser import TOTAL_GENE_OPTIONS
from .default_values import *
from ..app import app

INTRODUCTION_TEXT = "Mammalian brain cells are remarkably diverse in gene expression, anatomy, and function, " \
                    "yet the regulatory DNA landscape underlying this extensive heterogeneity is poorly understood. " \
                    "We carried out a comprehensive assessment of the epigenomes of mouse brain cell types by " \
                    "applying single nucleus DNA methylation sequencing (snmC-seq2) to profile 103,982 nuclei " \
                    "(including 95,815 neurons and 8,167 non-neuronal cells) from 45 regions of the mouse cortex, " \
                    "hippocampus, striatum, pallidum, and olfactory areas. We identified 161 cell clusters with " \
                    "distinct spatial locations and projection targets. In this browser, you can interactively " \
                    "explore this single cell methylome dataset in three different ways."

GENE_BROWSER_TEXT = 'Explore the methylation diversity of one gene at single-cell or cell-type level.'
GENE_BROWSER_IMG_URL = 'http://neomorph.salk.edu/omb_static/dissection_region_img/home_gene.jpg'

CELL_TYPE_BROWSER_TEXT = 'Explore the spatial distribution and methylation signature genes of one cell type.'
CELL_TYPE_BROWSER_IMG_URL = 'http://neomorph.salk.edu/omb_static/dissection_region_img/' \
                            'home_cell_type.jpg'

BRAIN_REGION_BROWSER_TEXT = 'Explore the cell type composition of adult mouse brain ' \
                            'dissection regions and anatomical structures.'
BRAIN_REGION_BROWSER_IMG_URL = 'http://neomorph.salk.edu/omb_static/dissection_region_img/' \
                               'home_brain_region.jpg'

ALL_CELL_TYPES = []
for col in ['CellClass', 'MajorType', 'SubType']:
    ALL_CELL_TYPES += dataset.get_variables(col).unique().tolist()
ALL_CELL_TYPES = sorted([i for i in ALL_CELL_TYPES if 'Outlier' not in i])

# References
LIU_2020_TEXT = 'Liu, Zhou et al. 2021. "DNA Methylation Atlas of the Mouse Brain at ' \
                'Single-Cell Resolution." Nature'
LIU_2020_URL = "https://www.nature.com/articles/s41586-020-03182-8"

LUO_2017_TEXT = "Luo, Keown et al. 2017. “Single-Cell Methylomes Identify Neuronal Subtypes " \
                "and Regulatory Elements in Mammalian Cortex.” Science"
LUO_2017_URL = "https://science.sciencemag.org/content/357/6351/600"

LUO_2018_TEXT = "Luo et al. 2018. “Robust Single-Cell DNA Methylome Profiling with snmC-seq2.” " \
                "Nature Communications"
LUO_2018_URL = "https://www.nature.com/articles/s41467-018-06355-2"

ABOUT_MARKDOWN = """
We are continually adding new functionality and improving documentation. 
If you have questions / suggestions / requirements about the browser or the dataset, 
please consider posting an issue on [github](https://github.com/lhqing/omb/issues/new).

------

This browser is made by [plotly-dash](https://dash.plotly.com/). 
See the source code of this browser on [github](https://github.com/lhqing/omb).
"""

jumbotron = dbc.Jumbotron(
    [
        html.H1("Brain Cell Methylation Viewer", className="display-6"),
        html.P(
            "DNA Methylation Atlas of the Mouse Brain at Single-Cell Resolution",
            className="lead",
        ),
        html.Hr(className="my-2"),
        html.P(
            INTRODUCTION_TEXT,
        )
    ]
)

app_cards = dbc.CardDeck(
    [
        # gene card
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.CardImg(src=GENE_BROWSER_IMG_URL, top=True),
                    html.H5("Gene", className="card-title m-3"),
                    html.P(GENE_BROWSER_TEXT, className="card-text mx-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id='gene-dropdown',
                                        placeholder='Input a gene name, e.g. Cux2',
                                        className='mr-3')
                                ],
                                width=10
                            ),
                            dbc.Col(
                                [
                                    html.A(
                                        dbc.Button(
                                            "GO",
                                            color="success"
                                        ),
                                        id='gene-url',
                                        href='gene?gene=Cux2'
                                    )
                                ],
                                width=10, lg=2  # width is 2 only on large screen
                            )
                        ],
                        className='m-3',
                        no_gutters=True
                    ),
                ],
                className='p-0 d-flex flex-column'
            )
        ),
        # brain region card
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.CardImg(src=BRAIN_REGION_BROWSER_IMG_URL, top=True),
                    html.H5("Brain Region", className="card-title m-3"),
                    html.P(BRAIN_REGION_BROWSER_TEXT, className="card-text mx-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        options=[
                                            {'label': region, 'value': region}
                                            for region in
                                            dataset.region_label_to_dissection_region_dict.keys()
                                        ],
                                        placeholder='Select a brain region.',
                                        id="brain-region-dropdown",
                                        value='Isocortex',
                                        className='mr-3'),
                                ],
                                width=10
                            ),
                            dbc.Col(
                                [
                                    html.A(
                                        dbc.Button(
                                            "GO",
                                            color="success"
                                        ),
                                        id='brain-region-url',
                                        href='brain_region?br=MOp'
                                    )
                                ],
                                width=10, lg=2
                            )
                        ],
                        className='m-3',
                        no_gutters=True
                    ),
                ],
                className='p-0 d-flex flex-column'
            )
        ),
        # cell type card
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.CardImg(src=CELL_TYPE_BROWSER_IMG_URL, top=True),
                    html.H5("Cell Type", className="card-title m-3"),
                    html.P(CELL_TYPE_BROWSER_TEXT, className="card-text mx-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Dropdown(id='cell-type-dropdown',
                                                 placeholder='Select a cell type.',
                                                 options=[{'label': ct, 'value': ct}
                                                          for ct in ALL_CELL_TYPES],
                                                 value='IT-L23',
                                                 className='mr-3')
                                ],
                                width=10
                            ),
                            dbc.Col(
                                [
                                    html.A(
                                        dbc.Button(
                                            "GO",
                                            color="success"
                                        ),
                                        id='cell-type-url',
                                        href='cell_type?ct=IT-L23'
                                    )
                                ],
                                width=10, lg=2
                            )
                        ],
                        className='m-3',
                        no_gutters=True
                    ),
                ],
                className='p-0 d-flex flex-column'
            )
        ),
    ]
)

info_cards = dbc.Row(
    [
        dbc.Col(
            [
                # reference
                dbc.Card(
                    [
                        dbc.CardHeader('Reference'),
                        dbc.Container(
                            [
                                html.H5('Main Reference', className='card-title'),
                                dbc.CardLink(LIU_2020_TEXT, href=LIU_2020_URL),
                                html.Hr(className="my-3"),
                                html.H5('About the snmC-seq2 Technology', className='card-title'),
                                html.P(dbc.CardLink(LUO_2017_TEXT, href=LUO_2017_URL)),
                                html.P(dbc.CardLink(LUO_2018_TEXT, href=LUO_2018_URL))
                            ],
                            className='p-3'
                        )
                    ],
                    className='h-100'
                ),
            ],
            width=12, lg=8
        ),
        dbc.Col(
            [
                # about
                dbc.Card(
                    [
                        dbc.CardHeader('About'),
                        dbc.CardBody(
                            [dcc.Markdown(ABOUT_MARKDOWN)]
                        )
                    ],
                    className='h-100'
                )
            ],
            width=12, lg=4
        )
    ],
    className='my-4'
)

layout = html.Div(
    children=[
        # first row is title and introduction
        jumbotron,
        # second row is link to three different browser
        app_cards,
        # third row is about reference
        info_cards
    ]
)


@app.callback(
    Output('gene-dropdown', 'options'),
    [Input('gene-dropdown', 'search_value')]
)
def update_gene_options(search_value):
    if not search_value:
        raise PreventUpdate

    this_options = [o for o in TOTAL_GENE_OPTIONS if search_value.lower() in o["label"].lower()]
    if len(this_options) > 100:
        return [{'label': 'Keep typing...', 'value': 'NOT A GENE', 'disabled': True}]
    else:
        return this_options


@app.callback(
    Output('gene-url', 'href'),
    [Input('gene-dropdown', 'value')]
)
def get_gene_url(gene_int):
    if gene_int:
        return f'gene?gene={gene_int}'
    else:
        raise PreventUpdate


@app.callback(
    Output('cell-type-url', 'href'),
    [Input('cell-type-dropdown', 'value')]
)
def get_cell_type_url(cell_type):
    if cell_type:
        return f'cell_type?ct={cell_type}'
    else:
        raise PreventUpdate


@app.callback(
    Output('brain-region-url', 'href'),
    [Input('brain-region-dropdown', 'value')]
)
def get_brain_region_url(brain_region):
    if brain_region:
        return f'brain_region?br={brain_region}'
    else:
        raise PreventUpdate
