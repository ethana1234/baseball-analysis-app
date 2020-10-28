import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from app import app

from . import batting_table

layout = dbc.Tabs([
    dbc.Tab(batting_table.layout, label='Batting'),
    dbc.Tab(html.Br(), label='Pitching'),
    dbc.Tab(html.Br(), label='Teams')
])
