"""
Main Dash apps
"""

import dash

APP_ROOT_NAME = 'omb'

app = dash.Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width"
        }
    ]
)

server = app.server
