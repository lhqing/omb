"""
Main Dash apps
"""
print('app.py start')

import dash

# external_stylesheets = ['https://raw.githubusercontent.com/lhqing/omb/master/omb/assets/s1.css',
#                        'https://raw.githubusercontent.com/lhqing/omb/master/omb/assets/styles.css']

APP_ROOT_NAME = 'omb'

print(__name__)

app = dash.Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width"
        }
    ],
    # external_stylesheets=external_stylesheets
)

server = app.server
