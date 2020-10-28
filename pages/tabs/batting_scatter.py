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
            id='b-scatter-team-name',
            options=[{'label': team_code, 'value': team_id} for team_code,team_id in team_id_dict.items()],
            placeholder='Team (default: PHI)',
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='b-scatter-season-year',
            options=[{'label': year, 'value': year} for year in range(2020, 2011, -1)],
            placeholder='Year (default: 2020)',
            searchable=False,
            multi=True,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='b-scatter-x',
            placeholder='X-axis Stat (default: BA)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='b-scatter-y',
            placeholder='Y-axis Stat (default: BA)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
    ]),
    html.Br(),
    html.Div(scatter_placeholder, id='b-scatter-result'),
    html.Div(id='b-save-scatter', style={'display': 'none'})
])

@app.callback(
    dash.dependencies.Output('b-save-scatter', 'children'),
    [dash.dependencies.Input('b-scatter-team-name', 'value'),
    dash.dependencies.Input('b-scatter-season-year', 'value'),]
)
def update_dataframe(team_ids, years):
    if team_ids is None or not team_ids:
        team_ids = [20]
    if years is None or not years:
        years = [2020]
    df = get_batters(team_ids, years)
    
    return df.to_json(orient='split')

@app.callback(
    [dash.dependencies.Output('b-scatter-result', 'children'),
    dash.dependencies.Output('b-scatter-x', 'options'),
    dash.dependencies.Output('b-scatter-y', 'options')],
    [dash.dependencies.Input('b-save-scatter', 'children'),
    dash.dependencies.Input('b-scatter-x', 'value'),
    dash.dependencies.Input('b-scatter-y', 'value'),
    dash.dependencies.Input('b-scatter-team-name', 'label'),
    dash.dependencies.Input('b-scatter-season-year', 'label')]
)
def update_scatter_data(data, x_axis, y_axis, team_names, seasons):

    if data is None:
        return scatter_placeholder, None, None
    else:
        if x_axis is None:
            x_axis = 'Age'
        if y_axis is None:
            y_axis = 'BA'
        df = pd.read_json(data, orient='split').round(3)
        fig = px.scatter(df, x=x_axis, y=y_axis)
        fig.update_traces(customdata=['Name'])
        fig.update_xaxes(title=x_axis, type='linear')
        fig.update_yaxes(title=y_axis, type='linear')
        axis_options = [{'label': col, 'value': col} for col in df.columns]
        return dcc.Graph(figure=fig), axis_options, axis_options

