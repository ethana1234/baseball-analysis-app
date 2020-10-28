import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from app import app

page_ids = ['home', 'scatters', 'tables', 'hello']

layout = html.Div(
    [
        html.H2("Menu", className="display-4"),
        html.Hr(),
        html.P(
            "Navigate to dashboards", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink('Home', href='/', id=f'{page_ids[0]}-link'),
                dbc.NavLink("Scatter Plot Tool", href="/scatters", id=f'{page_ids[1]}-link'),
                dbc.NavLink("Tables", href="/tables", id=f'{page_ids[2]}-link'),
                dbc.NavLink("Coming Soon", href="/hello", id=f'{page_ids[3]}-link'),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    },
)

@app.callback(
    [dash.dependencies.Output(f"{i}-link", "active") for i in page_ids],
    [dash.dependencies.Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        return True, False, False, False
    return [pathname == f'/{i}' for i in page_ids]
