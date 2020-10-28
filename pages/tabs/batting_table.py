import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3

from app import app
from db_scripts.db_connect import db_setup,db_error_cleanup
from data_insert import team_id_dict

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
    df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True)
    conn.close()

    df.drop(columns=['player_id', 'team_id'], inplace=True)

    return df


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
    df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True)
    conn.close()

    df.drop(columns=['team_id'], inplace=True)
    
    return df

def get_gamelogs(team_ids, years):
    conn = db_setup()
    query = f'''
        SELECT t1.team_code || CASE tbg.HomeAway WHEN 'H' THEN ' vs. ' ELSE ' @ ' END || t2.team_code Game, tbg.R || '-' || tbg.RunsAgainst Score, tbg.*
        FROM Teams t1 JOIN TeamBattingGame tbg
            ON t1.id=tbg.team_id
        JOIN Teams t2
            ON t2.id=tbg.opp_id
        WHERE t1.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
            AND tbg.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True)
    conn.close()

    df.drop(columns=['team_id', 'game_id', 'opp_id', 'HomeAway', 'RunsAgainst', 'R'], inplace=True)
    
    return df

table_placeholder = dbc.Jumbotron([
    dbc.Container([
            html.H1('Nothing Selected', className='display-3'),
            html.P('Select a table type to see data', className="lead"),
        ],
        fluid=True
    )
])


layout = html.Div(children=[
    html.H1('Batting Tables'),
    html.Div([
        dcc.Dropdown(
            id='b-table-type',
            options=[
                {'label': 'Player Season Batting', 'value': 'pbs'},
                {'label': 'Team Season Batting', 'value': 'tbs'},
                {'label': 'Team Batting Gamelogs', 'value': 'tbg'}
            ],
            placeholder='Table Type',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='b-team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team (default: PHI)',
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='b-season-year',
            options=[{'label': year, 'value': year} for year in [2020,2019,2018]],
            placeholder='Year (default: 2020)',
            searchable=False,
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Label('Sort By:'),
            dcc.Dropdown(id='b-sorter')
        ]),
        dbc.Col([
            dbc.Label(''),
            dbc.RadioItems(
                id='b-asc-desc',
                options=[
                    {'label': 'Ascending', 'value': True},
                    {'label': 'Descending', 'value': False}
                ]
            )
        ]),
    ]),
    html.Br(),
    html.Div(table_placeholder, id='b-table-result'),
    html.Div(id='b-save-table', style={'display': 'none'})
])

@app.callback(
    [dash.dependencies.Output('b-save-table', 'children'),
    dash.dependencies.Output('b-sorter', 'value'),
    dash.dependencies.Output('b-asc-desc', 'value')],
    [dash.dependencies.Input('b-table-type', 'value'),
    dash.dependencies.Input('b-team-name', 'value'),
    dash.dependencies.Input('b-season-year', 'value'),]
)
def update_dataframe(table_type, team_ids, years):
    if team_ids is None or not team_ids:
        team_ids = [20]
    if years is None or not years:
        years = [2020]
    if table_type == 'pbs':
        df = get_batters(team_ids, years)
    elif table_type == 'tbs':
        df = get_team_batting(team_ids, years)
    elif table_type == 'tbg':
        df = get_gamelogs(team_ids, years)
    else:
        return None, None, None
    
    return df.to_json(orient='split'), None, None

@app.callback(
    [dash.dependencies.Output('b-table-result', 'children'),
    dash.dependencies.Output('b-sorter', 'options')],
    [dash.dependencies.Input('b-save-table', 'children'),
    dash.dependencies.Input('b-sorter', 'value'),
    dash.dependencies.Input('b-asc-desc', 'value')]
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
    
