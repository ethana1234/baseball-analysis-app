import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from app import app
from .tabs import batting_time_series,pitching_time_series

layout = dbc.Tabs([
    dbc.Tab(batting_time_series.layout, label='Batting'),
    dbc.Tab(pitching_time_series.layout, label='Pitching')
])
