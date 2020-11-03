import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import pandas as pd

from app import app
import db_scripts.graph_data_query as query_engine
from data_insert import team_id_dict

table_placeholder = dbc.Jumbotron([
    dbc.Container([
            html.H1('Nothing Selected', className='display-3'),
            html.P('Select a table type to see data', className="lead"),
        ],
        fluid=True
    )
])


layout = html.Div(children=[
    html.H1('Pitching Tables'),
    html.Div([
        dcc.Dropdown(
            id='p-table-type',
            options=[
                {'label': 'Player Season Pitching', 'value': 'pps'},
                {'label': 'Team Season Pitching', 'value': 'tps'},
                {'label': 'Team Pitching Gamelogs', 'value': 'tbg'}
            ],
            placeholder='Table Type',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-table-team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team (default: PHI)',
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='p-table-season-year',
            options=[{'label': year, 'value': year} for year in range(2020, 2011, -1)],
            placeholder='Year (default: 2020)',
            searchable=False,
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Label('Sort By:'),
            dcc.Dropdown(id='p-table-sorter')
        ]),
        dbc.Col([
            dbc.Label(''),
            dbc.RadioItems(
                id='p-table-asc-desc',
                options=[
                    {'label': 'Ascending', 'value': True},
                    {'label': 'Descending', 'value': False}
                ]
            )
        ]),
    ]),
    html.Br(),
    html.Div(table_placeholder, id='p-table-result'),
    html.Div(id='p-table-save', style={'display': 'none'})
])

@app.callback(
    [Output('p-table-save', 'children'),
    Output('p-table-sorter', 'value'),
    Output('p-table-asc-desc', 'value')],
    [Input('p-table-type', 'value'),
    Input('p-table-team-name', 'value'),
    Input('p-table-season-year', 'value'),]
)
def update_dataframe(table_type, team_ids, years):
    if team_ids is None or not team_ids:
        team_ids = [20]
    if years is None or not years:
        years = [2020]
    if table_type == 'pps':
        df = query_engine.get_players(team_ids, years, 'p')
        df.drop(columns=['player_id', 'team_id'], inplace=True)

    elif table_type == 'tps':
        df = query_engine.get_team_season(team_ids, years, 'p')
        df.drop(columns=['team_id'], inplace=True)

    elif table_type == 'tpg':
        df = query_engine.get_gamelogs(team_ids, years, 'p')
        df.drop(columns=['team_id', 'game_id', 'opp_id', 'HomeAway', 'RunsFor', 'R'], inplace=True)

    else:
        return None, None, None
    
    return df.to_json(orient='split'), None, None

@app.callback(
    [Output('p-table-result', 'children'),
    Output('p-table-sorter', 'options')],
    [Input('p-table-save', 'children'),
    Input('p-table-sorter', 'value'),
    Input('p-table-asc-desc', 'value')]
)
def update_table_type(data, sort_by, asc_desc):
    if data is None:
        table, sorter = table_placeholder, []
    else:
        df = pd.read_json(data, orient='split').round(3)
        if sort_by is not None:
            # Table is getting sorted
            df = df.sort_values(by=[sort_by], ascending=asc_desc)
        table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, style={'font-size': 11})
        sorter = [{'label': col, 'value': col} for col in df.columns]

    return table, sorter
    
