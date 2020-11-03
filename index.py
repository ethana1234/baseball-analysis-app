import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output

import sys,requests,json,hashlib
from requests.exceptions import HTTPError

from app import app
from pages import tables,scatter_plots,time_series
import sidebar

server = app.server

debug = True

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar.layout,
    html.Div(id='page-content', style={
        "margin-left": "18rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    })
])

index_page = html.Div([
    html.H1('Baseball Data Visualization App', id='index-header'),
    html.P(['By Ethan Agranoff ',
        html.A('(@ethana1234 on GitHub)', href='https://github.com/ethana1234')],
        id='index-author',
        style={'font-size': '20px'}),
    html.Img(src=app.get_asset_url('ballpark.jpg'), style={'max-width': '100%', 'max_height': '90%'})
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/scatters':
        return scatter_plots.layout
    elif pathname == '/tables':
        return tables.layout
    elif pathname == '/ts':
        return time_series.layout
    else:
        return index_page

if __name__=='__main__':
    app.run_server(debug=debug)
