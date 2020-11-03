import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import pandas as pd

from app import app
import db_scripts.graph_data_query as query_engine
from data_insert import team_id_dict
from .graphing import build_scatter

scatter_placeholder = dbc.Spinner(color='secondary')

layout = html.Div(children=[
    html.Div([
        dcc.Dropdown(
            id='p-scatter-team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team (default: PHI)',
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-scatter-season-year',
            options=[{'label': year, 'value': year} for year in range(2020, 2011, -1)],
            placeholder='Year (default: 2020)',
            searchable=False,
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-scatter-x',
            placeholder='X-axis Stat (default: Age)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-scatter-y',
            placeholder='Y-axis Stat (default: ERA)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dbc.Checklist(
            options=[{'label': 'Qualified pitchers only', 'value': 1}],
            value=[],
            id='p-scatter-qualified',
            style={'padding-left': '25px'}
        ),
    ], style={'display': 'flex'}),
    html.Br(),
    html.H3(id='p-scatter-label', style={'text-align': 'center'}),
    html.Div(scatter_placeholder, id='p-scatter-result'),
    html.Div(id='p-scatter-save', style={'display': 'none'}),
    html.Footer('*Note that Pearson Correlation may not useful for some variables')
])

@app.callback(
    Output('p-scatter-save', 'children'),
    [Input('p-scatter-team-name', 'value'),
    Input('p-scatter-season-year', 'value'),]
)
def update_dataframe(team_ids, years):
    if team_ids is None or not team_ids:
        team_ids = [20]
    if years is None or not years:
        years = [2020]
    df = query_engine.get_players(team_ids, years, 'p')

    df.drop(columns=['player_id', 'team_id'], inplace=True)
    
    return df.to_json(orient='split')

@app.callback(
    [Output('p-scatter-result', 'children'),
    Output('p-scatter-x', 'options'),
    Output('p-scatter-y', 'options'),
    Output('p-scatter-label', 'children')],
    [Input('p-scatter-save', 'children'),
    Input('p-scatter-x', 'value'),
    Input('p-scatter-y', 'value'),
    Input('p-scatter-season-year', 'value'),
    Input('p-scatter-qualified', 'value')]
)
def update_scatter_data(data, x_axis, y_axis, seasons, qualified):
    if data is None:
        return scatter_placeholder, None, None
    if x_axis is None:
        x_axis = 'Age'
    if y_axis is None:
        y_axis = 'ERA'
    df = pd.read_json(data, orient='split').round(3)
    if qualified:
        # More efficient way to filter this?
        df1 = df[(df.IP >= 60) & (df.season == 2020)]
        df2 = df[df.IP > 162]
        df = pd.concat([df1,df2])
    return build_scatter(df, x_axis, y_axis, seasons)
