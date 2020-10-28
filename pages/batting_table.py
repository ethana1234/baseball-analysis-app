import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3

from app import app
from db_scripts.db_connect import db_setup,db_error_cleanup
from data_insert import team_id_dict

# TODO: Use local variable to sort by a column

def get_batters(team_ids, years):
    conn = db_setup()
    query = f'''
        SELECT b.Name, b.Pos, b.Handedness, t.team_code Team, pbs.*
        FROM Teams t JOIN PlayerBattingSeason pbs
            ON t.id=pbs.team_id
        JOIN Batters b
            ON pbs.player_id=b.id
        WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
            AND pbs.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True).round(3)
    conn.close()

    df.drop(columns=['player_id', 'team_id'], inplace=True)

    current_table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, style={'font-size': 11})
    return current_table


def get_team_batting(team_ids, years):
    conn = db_setup()
    query = f'''
        SELECT t.Name, (ts.wins || '-' || ts.losses) as Record, tbs.*
        FROM Teams t JOIN TeamBattingSeason tbs
            ON t.id=tbs.team_id
        JOIN TeamSeason ts
            ON t.id=ts.team_id
                AND ts.season=tbs.season
        WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
            AND tbs.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True).round(3)
    conn.close()

    df.drop(columns=['team_id'], inplace=True)

    current_table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, style={'font-size': 11})
    
    return current_table

table_placeholder = dbc.Jumbotron([
    dbc.Container([
            html.H1('Nothing Selected', className='display-3'),
            html.P('Select a table type to see data', className="lead"),
        ],
        fluid=True
    )
])

current_table = table_placeholder


layout = html.Div(children=[
    html.H1('Batting Tables'),
    html.Div([
        dcc.Dropdown(
            id='table-type',
            options=[
                {'label': 'Player Season Batting', 'value': 'pbs'},
                {'label': 'Team Season Batting', 'value': 'tbs'},
                {'label': 'Team Game Batting', 'value': 'tbg'}
            ],
            placeholder='Table Type',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team (default: PHI)',
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='season-year',
            options=[{'label': year, 'value': year} for year in [2020,2019,2018]],
            placeholder='Year (default: 2020)',
            searchable=False,
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
    ]),
    html.Div(current_table, id='table-result')
])

@app.callback(
    dash.dependencies.Output('table-result', 'children'),
    [dash.dependencies.Input('table-type', 'value'),
    dash.dependencies.Input('team-name', 'value'),
    dash.dependencies.Input('season-year', 'value')]
)
def update_table_type(table_type, team_ids, years):
    if team_ids is None:
        team_ids = [20]
    if years is None:
        years = [2020]
    if table_type == 'pbs':
        return get_batters(team_ids, years)
    elif table_type == 'tbs':
        return get_team_batting(team_ids, years)
    else:
        return table_placeholder
    
