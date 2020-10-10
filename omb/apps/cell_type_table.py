import dash_bootstrap_components as dbc
import dash_html_components as html

from .default_values import *
from .home import LIU_2020_URL
from ..app import APP_ROOT_NAME

cell_type_df = dataset.cell_type_table.reset_index()

formal_name_to_internal_name = {v: k for k, v in dataset.cell_type_table['FormalName'].items()}
# Parent was internal name, turn it into formal names (have special character, etc.)
cell_type_df['Parent'] = cell_type_df['Parent'].map(cell_type_df.set_index('UniqueName')['FormalName'])

COLUMNS_ORDER = ['FormalName', 'Cluster Level', 'Parent',
                 'Signature Genes', 'Number of total cells', 'Description']
cell_type_df = cell_type_df[COLUMNS_ORDER].copy()


# Turn brain region name into links
def name_to_link(name):
    if isinstance(name, float):
        return ''
    internal_name = formal_name_to_internal_name[name].replace(' ', '%20')
    return html.A(name, href=f'/{APP_ROOT_NAME}cell_type?ct={internal_name}')


def prepare_row(row):
    row_html = html.Tr(
        [
            html.Td(name_to_link(row['FormalName'])),
            html.Td(row['Cluster Level']),
            html.Td(name_to_link(row['Parent'])),
            html.Td(row['Signature Genes']),
            html.Td(row['Number of total cells']),
            html.Td(row['Description'])
        ]
    )
    return row_html


def create_cell_type_table_layout():
    # prepare table
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th('Name'),
                    html.Th('Cluster Level'),
                    html.Th('Parent'),
                    html.Th('Signature Genes', style={'width': '20%'}),
                    html.Th('Number of Cells'),
                    html.Th('Description')
                ]
            )
        )
    ]
    rows = cell_type_df.apply(prepare_row, axis=1).tolist()
    table_body = [html.Tbody(rows)]

    table = dbc.Table(table_header + table_body,
                      striped=True,
                      bordered=True,
                      hover=True)

    cell_type_table_app_layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Jumbotron(
                        [
                            html.H1('Cell Type Table'),
                            html.P(
                                [
                                    f'This table listed all the cell types identified in this study. '
                                    f'In the three-level iterative clustering analysis, we identified '
                                    f'and annotated a total of 3 cell classes, 41 major cell types, and 161 subtypes. '
                                    f'You can click their names to view their spatial distribution or signature genes '
                                    f'in the cell type viewer. For more details, please see ',
                                    html.A('the manuscript', href=LIU_2020_URL),
                                    f'.'
                                ]
                            )
                        ],
                        className='w-100'
                    )
                ],
                className='px-5'
            ),
            dbc.Row(
                [
                    table
                ],
                className='px-5'
            )
        ]
    )
    return cell_type_table_app_layout

