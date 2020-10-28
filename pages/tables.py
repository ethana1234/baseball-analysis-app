import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from app import app

from .tabs import batting_table,pitching_table

layout = dbc.Tabs([
    dbc.Tab(batting_table.layout, label='Batting'),
    dbc.Tab(pitching_table.layout, label='Pitching')
])
