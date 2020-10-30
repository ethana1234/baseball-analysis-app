import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np

from app import app
from db_scripts.db_connect import db_setup,db_error_cleanup
from data_insert import team_id_dict

ts_placeholder = dbc.Spinner(color='secondary')

def get_gamelogs(team_ids, year):
    conn = db_setup()
    query = f'''
        SELECT t1.team_code Team, tpg.*
        FROM Teams t1 JOIN TeamPitchingGame tpg
            ON t1.id=tpg.team_id
        JOIN Teams t2
            ON t2.id=tpg.opp_id
        WHERE t1.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
            AND tpg.season=?'''
    df = pd.read_sql_query(query, conn, params=[*team_ids, year], coerce_float=True)
    conn.close()

    df.drop(columns=['team_id', 'game_id', 'opp_id', 'HomeAway', 'season'], inplace=True)
    df['Run Differential'] = df.RunsFor - df.R
    
    return df

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
    dash.dependencies.Output('p-ts-save', 'children'),
    [dash.dependencies.Input('p-ts-team-name', 'value'),
    dash.dependencies.Input('p-ts-season', 'value')]
)
def update_dataframe(team_ids, year):
    if team_ids is None or not team_ids:
        team_ids = [20]
    df = get_gamelogs(team_ids, year)
    
    return df.to_json(orient='split')

@app.callback(
    [dash.dependencies.Output('p-ts-result', 'children'),
    dash.dependencies.Output('p-ts-y', 'options'),
    dash.dependencies.Output('p-ts-label', 'children')],
    [dash.dependencies.Input('p-ts-save', 'children'),
    dash.dependencies.Input('p-ts-y', 'value')]
)
def update_ts_data(data, y_axis):
    if data is None:
        return ts_placeholder, None, None
    else:
        if y_axis is None:
            y_axis = 'ERA'
        df = pd.read_json(data, orient='split').round(3)
        df.game_date = pd.to_datetime(df.game_date, format='%Y-%m-%d').dt.to_pydatetime()
        fig = px.line(df, x='game_date', y=y_axis, color='Team')
        fig.update_layout(
            font=dict(
                size=18,
                family='Segoe UI'
            ),
            hovermode='x',
            hoverdistance=100,
            spikedistance=1000,
            xaxis=dict(
                title='Game Date',
                showspikes=True,
                spikemode='across',
                spikethickness=2,
                spikedash='dot',
                spikecolor='grey'
            ),
            yaxis=dict(title=y_axis)
        )
        if y_axis == 'ERA':
            fig.update_traces(hovertemplate='%{y:1.2f}')
        elif y_axis == 'IP':
            fig.update_traces(hovertemplate='%{y:.1f}')
        else:
            fig.update_traces(hovertemplate='%{y:d}')
        # Make sure to only have numeric columns as axis options
        axis_options = list(df.select_dtypes(include=[np.number]).columns.values)
        axis_options = [{'label': col, 'value': col} for col in axis_options]
        ts_title = f'Time Series for {y_axis}'
        return dcc.Graph(figure=fig, style={'height': '80vh'}), axis_options, ts_title
    
