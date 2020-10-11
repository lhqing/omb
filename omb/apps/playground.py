# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div(children=[
    html.H4(children='Excel-like checkboxes'),
    dcc.Checklist(
        id='all',
        options=[{'label': 'all', 'value': 'all'}],
        value=[]
    ),
    dcc.Checklist(
        id='cities',
        options=[
            {'label': 'New York City', 'value': 'NYC'},
            {'label': 'Montréal', 'value': 'MTL'},
            {'label': 'San Francisco', 'value': 'SF'}
        ],
        value=['MTL', 'SF']
    ),
    html.Div(id='loop_breaker_container', children=[])
])


@app.callback(Output('cities', 'value'),
              [Input('all', 'value')])
def update_cities(inputs):
    if len(inputs) == 0:
        return []
    else:
        return ['NYC', 'MTL', 'SF']


@app.callback(Output('loop_breaker_container', 'children'),
              [Input('cities', 'value')],
              [State('all', 'value')])
def update_all(inputs, _):
    states = dash.callback_context.states
    if len(inputs) == 3 and states['all.value'] == []:
        return [html.Div(id='loop_breaker', children=True)]
    elif len(inputs) == 0 and states['all.value'] == ['all']:
        return [html.Div(id='loop_breaker', children=False)]
    else:
        return []


@app.callback(Output('all', 'value'),
              [Input('loop_breaker', 'children')])
def update_loop(all_true):
    if all_true:
        return ['all']
    else:
        return []


if __name__ == '__main__':
    app.run_server(debug=True, port='1234')
