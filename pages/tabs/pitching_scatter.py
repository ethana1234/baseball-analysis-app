import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3

from app import app
from db_scripts.db_connect import db_setup,db_error_cleanup
from data_insert import team_id_dict

scatter_placeholder = dbc.Jumbotron([
    dbc.Container([
            html.H1('Nothing Selected', className='display-3'),
            html.P('Select a graph type to see data', className="lead"),
        ],
        fluid=True
    )
])

layout = html.Div(children=[
    html.Div([
        dcc.Dropdown(
            id='p-scatter-team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team',
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-scatter-season-year',
            options=[{'label': year, 'value': year} for year in range(2020, 2011, -1)],
            placeholder='Year',
            searchable=False,
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-scatter-x',
            placeholder='X-axis Stat (default: BA)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-scatter-y',
            placeholder='Y-axis Stat (default: BA)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
    ]),
    html.Br(),
    html.Div(scatter_placeholder, id='p-scatter-result'),
    html.Div(id='p-save-scatter', style={'display': 'none'})
])
