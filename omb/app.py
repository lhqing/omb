"""
Main Dash apps
"""

import dash

APP_ROOT_NAME = 'omb'

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width"
        }
    ]
)
app.title = 'mC Browser'
server = app.server
