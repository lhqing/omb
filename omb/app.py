"""
Main Dash apps
"""

import dash

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
app.config.suppress_callback_exceptions = True

# this is only based on my own server
# server deploy setting, change APP_NAME based on the routing config in apache
# APP_NAME = 'omb'
# app.config.update({
#     # remove the default of '/'
#     'routes_pathname_prefix': f'/{APP_NAME}/',
#
#     # remove the default of '/'
#     'requests_pathname_prefix': f'/{APP_NAME}/'
# })

