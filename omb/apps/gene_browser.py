import dash_html_components as html
import dash_core_components as dcc
import dash_table

URL = """http://neomorph.salk.edu/mouse_brain.php?location=2:10000000-10100000&active=["12_2","14_3","15_2","15_3","15_1","15_4"]&config=[{type:"MethTrack",height:50,class:"-CG CH -coverage"},{id:"12_2",color:{CH:"C8CA86",rColor:1}},{id:"12_3",color:{CH:"475400",rColor:1}},{id:"12_4",color:{CH:"94B400",rColor:1}},{id:"12_1",color:{CH:"212900",rColor:1}},{id:"13_2",color:{CH:"A8D617",rColor:1}},{id:"13_1",color:{CH:"B3D164",rColor:1}},{id:"14_3",color:{CH:"435F00",rColor:1}},{id:"14_1",color:{CH:"A6D648",rColor:1}},{id:"14_2",color:{CH:"203900",rColor:1}},{id:"15_4",color:{CH:"6DC600",rColor:1}},{id:"15_3",color:{CH:"42A100",rColor:1}},{id:"15_1",color:{CH:"3BB800",rColor:1}},{id:"15_2",color:{CH:"167600",rColor:1}}]&settings={accordion:"hide",}"""


def create_gene_browser_layout():
    layout = html.Div(children=[
        # first row is gene info and gene like me table
        html.Div(children=[
            html.Div(children=[
                html.H5('GENE', id='gene_name')
            ], className='pretty_container five columns'),
            html.Div(children=[
                dash_table.DataTable(id='genes_like_me_table')
            ], className='pretty_container seven columns'),
        ], className='row container-display'),

        # second row is barplot
        html.Div(children=[
            html.Div(children=[
                html.H6('Gene Plots Control'),
                html.P('Scatter Coords'),
                dcc.Dropdown(id='scatter_coords'),
                html.P('Cluster Level'),
                dcc.Dropdown(id='cluster_level'),
                html.P('Color Range'),
                dcc.RangeSlider(id='color_range_slider')
            ], className='pretty_container three columns'),
            html.Div(children=[
                html.H6('Gene mC Rate Scatter Plot'),
                dcc.Graph(id='gene_scatter_plot'),
            ], className='pretty_container five columns'),
            html.Div(children=[
                html.H6('Gene mC Rate Sunburst Plot'),
                dcc.Graph(id='gene_sunburst_plot'),
            ], className='pretty_container four columns')
        ], className='row container-display'),

        # third row is gene scatter and sunburst
        html.Div(children=[
            html.H6('Gene - Cell Type Violin Plot'),
            dcc.Graph(id='gene_violin_plot')
        ], className='pretty_container twelve columns'),

        # forth row is annoj browser control
        html.Div(children=[
            html.H6('AnnoJ Genome Browser', id='annoj_title'),
            html.Div(children=[
                html.Div(children=[
                    html.Div(children=[html.P('Color By Cell Type'), ], className='row'),
                    html.P('Hide toolbar'),
                ], className='two columns')
            ], className='row container-display'),
        ], className='pretty_container twelve columns'),
        # fifth row is annoj browser
        html.Iframe(src=URL, id='annoj_iframe',
                    width='100%', height='520px',
                    className='twelve columns')

    ])

    return layout
