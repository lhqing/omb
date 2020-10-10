import dash_bootstrap_components as dbc
import dash_html_components as html

from .default_values import *
from .home import LIU_2020_URL
from ..app import APP_ROOT_NAME

brain_region_df = dataset.brain_region_table.reset_index()

COLUMNS_ORDER = ['Region Name', 'Sub-Region', 'Major Region',
                 'Slice', 'Number of total cells', 'Dissection Region ID',
                 'Detail Region', 'Potential Overlap']
brain_region_df = brain_region_df[COLUMNS_ORDER].copy()


# Turn brain region name into links
def name_to_link(name):
    return html.A(name, href=f'/{APP_ROOT_NAME}brain_region?br={name}')


def prepare_row(row):
    row_html = html.Tr(
        [
            html.Td(name_to_link(row['Region Name'])),
            html.Td(name_to_link(row['Sub-Region'])),
            html.Td(name_to_link(row['Major Region'])),
            html.Td(row['Slice']),
            html.Td(row['Number of total cells']),
            html.Td(row['Dissection Region ID']),
            html.Td(row['Detail Region']),
            html.Td(row['Potential Overlap'])
        ]
    )
    return row_html


def create_brain_table_layout():
    # prepare table
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th('Name'),
                    html.Th('Sub-Region'),
                    html.Th('Major Region'),
                    html.Th('Slice'),
                    html.Th('Number of Cells'),
                    html.Th('Dissection Region ID'),
                    html.Th('Detail Anatomical Structures'),
                    html.Th('Potentially Overlapped With')
                ]
            )
        )
    ]
    rows = brain_region_df.apply(prepare_row, axis=1).tolist()
    table_body = [html.Tbody(rows)]

    table = dbc.Table(table_header + table_body,
                      striped=True,
                      bordered=True,
                      hover=True)

    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Jumbotron(
                        [
                            html.H1('Dissection Region Table'),
                            html.P(
                                [
                                    f'This table listed {brain_region_df.shape[0]} brain dissection regions included '
                                    f'in this study. All the tissues were dissected from Adult (P56) C57BL/6J '
                                    f'male mice brain. You can click their names to view their '
                                    f'structure and cell-type composition in the brain region viewer. '
                                    f'For more details, please see ',
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
    return layout
