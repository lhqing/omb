"""
Main Dash apps
"""

import dash
import subprocess

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
app.title = 'mC Viewer'
server = app.server

# judge which server I am running and change the prefix
host_name = subprocess.run(['hostname'], stdout=subprocess.PIPE, encoding='utf-8').stdout.strip()
if host_name.lower().startswith('neomorph'):
    ON_NEOMORPH = True
else:
    ON_NEOMORPH = False
