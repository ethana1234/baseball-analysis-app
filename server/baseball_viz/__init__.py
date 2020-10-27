import dash
import dash_bootstrap_components as dbc
from .dashboard import create_dashboard

def init_dashboard(server):
    dash_app = dash.Dash(
        server=server,
        #routes_pathname_prefix='/dashapp/',
        external_stylesheets=[dbc.themes.SOLAR]
    )
    return create_dashboard(dash_app)

