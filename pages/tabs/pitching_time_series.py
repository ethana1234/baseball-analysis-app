import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

from app import app
import db_scripts.graph_data_query as query_engine
from data_insert import team_id_dict
from .graphing import build_time_series

ts_placeholder = dbc.Spinner(color='secondary')

layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='p-ts-team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team (default: PHI)',
            multi=True,
            style={'width': 600, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-ts-y',
            placeholder='Stat (default: ERA)',
            searchable=False,
            style={'width': 600, 'display': 'inline-block'}
        ),
    ]),
    html.Div([
        dbc.FormGroup([
            dbc.Label('Season', html_for='p-ts-season'),
            dcc.Slider(
                id='p-ts-season',
                min=2012,
                max=2020,
                step=1,
                marks={year: str(year) for year in range(2012, 2021)},
                value=2020
            )
        ])
    ]),
    html.Br(),
    html.H3(id='p-ts-label', style={'text-align': 'center'}),
    html.Div(ts_placeholder, id='p-ts-result'),
    html.Div(id='p-ts-save', style={'display': 'none'})
])

@app.callback(
    Output('p-ts-save', 'children'),
    [Input('p-ts-team-name', 'value'),
    Input('p-ts-season', 'value')]
)
def update_dataframe(team_ids, year):
    if team_ids is None or not team_ids:
        team_ids = [20]
    df = query_engine.get_gamelogs(team_ids, [year], 'p')

    df.drop(columns=['team_id', 'game_id', 'opp_id', 'HomeAway', 'season', 'Game', 'Score'], inplace=True)
    df['Run Differential'] = df.RunsFor - df.R
    
    return df.to_json(orient='split')

@app.callback(
    [Output('p-ts-result', 'children'),
    Output('p-ts-y', 'options'),
    Output('p-ts-label', 'children')],
    [Input('p-ts-save', 'children'),
    Input('p-ts-y', 'value'),
    Input('p-ts-team-name', 'value')]
)
def update_ts_data(data, y_axis, team_ids):
    if data is None:
        return ts_placeholder, None, None
    if y_axis is None:
        y_axis = 'ERA'
    df = pd.read_json(data, orient='split').round(3)
    return build_time_series(df, y_axis, team_ids, '%{y:.2f}' if y_axis == 'ERA' else ('%{y:.1f}' if y_axis == 'IP' else '%{y:d}'))
    
