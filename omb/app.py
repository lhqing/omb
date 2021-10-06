"""
Main Dash apps
"""

import dash
import subprocess

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

# Add google analytics
app.index_string = '''<!DOCTYPE html>
<html>
<head>
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ZP9XN3P2WK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-ZP9XN3P2WK');
</script>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>
'''

server = app.server

# judge which server I am running and change the prefix
host_name = subprocess.run(['hostname'], stdout=subprocess.PIPE, encoding='utf-8').stdout.strip()
if host_name.lower().startswith('neomorph'):
    ON_NEOMORPH = True
    APP_ROOT_NAME = 'omb/'
else:
    ON_NEOMORPH = False
    APP_ROOT_NAME = ''

