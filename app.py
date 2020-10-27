import dash
import dash_bootstrap_components as dbc
from flask_cors import CORS

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = '@ethana1234 BB App'
CORS(app.server, resources={r'/*': {'origins': '*'}})
server = app.server
