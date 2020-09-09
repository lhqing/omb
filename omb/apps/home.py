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
                    "applying single nucleus DNA methylation sequencing (snmC-seq2) to profile 110,294 nuclei " \
                    "(including 95,815 neurons and 8,167 non-neuronal cells) from 45 regions of the mouse cortex, " \
                    "hippocampus, striatum, pallidum, and olfactory areas. We identified 161 cell clusters with " \
                    "distinct spatial locations and projection targets. In this browser, you can interactively " \
                    "explore this single cell methylome dataset in three different ways."

GENE_BROWSER_TEXT = 'Explore the methylation diversity of one gene at single-cell or cell-type level.'
GENE_BROWSER_IMG_URL = 'https://github.com/lhqing/omb/raw/master/omb/assets/dissection_region_img/home_gene.jpg'

CELL_TYPE_BROWSER_TEXT = 'Explore the spatial distribution and methylation signature genes of one cell type.'
CELL_TYPE_BROWSER_IMG_URL = 'https://github.com/lhqing/omb/raw/master/omb/assets/' \
                            'dissection_region_img/home_cell_type.jpg'

BRAIN_REGION_BROWSER_TEXT = 'Explore the cell type composition of adult mouse brain ' \
                            'dissection regions and anatomical structures.'
BRAIN_REGION_BROWSER_IMG_URL = 'https://github.com/lhqing/omb/raw/master/omb/assets/' \
                               'dissection_region_img/home_brain_region.jpg'

ALL_CELL_TYPES = []
for col in ['CellClass', 'MajorType', 'SubType']:
    ALL_CELL_TYPES += dataset.get_variables(col).unique().tolist()
ALL_CELL_TYPES = sorted([i for i in ALL_CELL_TYPES if 'Outlier' not in i])

REFERENCE_MARKDOWN = """
* Main reference: 
    * [Liu, Zhou et al. 2020. “DNA Methylation Atlas of the Mouse Brain at Single-Cell Resolution.” bioRxiv](https://www.biorxiv.org/content/10.1101/2020.04.30.069377v1)
* About the snmC-seq2 Technology:
    * [Luo, Keown et al. 2017. “Single-Cell Methylomes Identify Neuronal Subtypes and Regulatory Elements in Mammalian Cortex.” Science](https://science.sciencemag.org/content/357/6351/600)
    * [Luo et al. 2018. “Robust Single-Cell DNA Methylome Profiling with snmC-seq2.” Nature Communications](https://www.nature.com/articles/s41467-018-06355-2) 
"""

ABOUT_MARKDOWN = """
We are continually adding new functionality and improving documentation. 
If you have questions / suggestions / requirements about the browser or the dataset, 
please consider posting an issue on [github](https://github.com/lhqing/omb/issues/new).

------

This browser is made by [plotly-dash](https://dash.plotly.com/). 
See the source code of this browser on [github](https://github.com/lhqing/omb).
"""

layout = html.Div(children=[
    # first row is title and introduction
    html.Div(children=[
        html.H1('DNA Methylation Atlas of the Mouse Brain at Single-Cell Resolution',
                style={'font-size': '2.5em', 'text-align': 'center'}),
        html.P(INTRODUCTION_TEXT)
    ], className='pretty_container'),

    # second row is link to three different browser
    html.Div(children=[
        html.Div(children=[
            html.Img(src=GENE_BROWSER_IMG_URL, style={'width': '100%'}),
            html.H4('Gene Browser'),
            html.P(GENE_BROWSER_TEXT),
            html.Div(children=[
                dcc.Dropdown(id='gene-dropdown',
                             placeholder='Input a gene name, e.g. Cux2',
                             className='nine columns'),
                html.A(html.Button(children='GO'), id='gene-url', href='gene?gene=Cux2')
            ], className='row'),
        ], className='four columns pretty_container'),
        html.Div(children=[
            html.Img(src=BRAIN_REGION_BROWSER_IMG_URL, style={'width': '100%'}),
            html.H4('Brain Region Browser'),
            html.P(BRAIN_REGION_BROWSER_TEXT),
            html.Div(children=[
                dcc.Dropdown(options=[{'label': region, 'value': region}
                                      for region in dataset.region_label_to_dissection_region_dict.keys()],
                             placeholder='Select a brain region.',
                             id="brain-region-dropdown",
                             className='nine columns'),
                html.A(html.Button(children='GO'), id='brain-region-url', href='brain_region?br=MOp')
            ], className='row')
        ], className='four columns pretty_container'),
        html.Div(children=[
            html.Img(src=CELL_TYPE_BROWSER_IMG_URL, style={'width': '100%'}),
            html.H4('Cell Type Browser'),
            html.P(CELL_TYPE_BROWSER_TEXT),
            html.Div(children=[
                dcc.Dropdown(id='cell-type-dropdown',
                             placeholder='Select a cell type.',
                             options=[{'label': ct, 'value': ct}
                                      for ct in ALL_CELL_TYPES],
                             className='nine columns'),
                html.A(html.Button(children='GO'), id='cell-type-url', href='cell_type?ct=IT-L23')
            ], className='row'),
        ], className='four columns pretty_container'),
    ], className='row container-display'),

    # third row is about reference
    html.Div(children=[
        html.Div(children=[
            html.H5('Reference'),
            dcc.Markdown(REFERENCE_MARKDOWN),
        ], className='pretty_container six columns'),
        html.Div(children=[
            html.H5('About'),
            dcc.Markdown(ABOUT_MARKDOWN)
        ], className='pretty_container six columns')
    ], className='row container-display')
], className='offset-by-one column ten columns')


@app.callback(
    Output('gene-dropdown', 'options'),
    [Input('gene-dropdown', 'search_value')]
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
