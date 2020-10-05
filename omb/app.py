"""
Main Dash apps
"""

import dash
import dash_bootstrap_components as dbc

APP_ROOT_NAME = 'omb'

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    # external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width"
        }
    ]
)
app.title = 'mC Viewer'
server = app.server
