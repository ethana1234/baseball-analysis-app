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

scatter_placeholder = dbc.Spinner(color='secondary')

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
            placeholder='X-axis Stat (default: Age)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='b-scatter-y',
            placeholder='Y-axis Stat (default: BA)',
            searchable=False,
            style={'width': 300, 'display': 'inline-block'}
        ),
        dbc.Checklist(
            options=[{'label': 'Qualified batters only', 'value': 1}],
            value=[],
            id='b-scatter-qualified',
            style={'padding-left': '25px'}
        ),
    ], style={'display': 'flex'}),
    html.Br(),
    html.H3(id='b-scatter-label', style={'text-align': 'center'}),
    html.Div(scatter_placeholder, id='b-scatter-result'),
    html.Div(id='b-scatter-save', style={'display': 'none'}),
    html.Footer('*Note that Pearson Correlation may not useful for some variables')
])

@app.callback(
    dash.dependencies.Output('b-scatter-save', 'children'),
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
    dash.dependencies.Output('b-scatter-y', 'options'),
    dash.dependencies.Output('b-scatter-label', 'children')],
    [dash.dependencies.Input('b-scatter-save', 'children'),
    dash.dependencies.Input('b-scatter-x', 'value'),
    dash.dependencies.Input('b-scatter-y', 'value'),
    dash.dependencies.Input('b-scatter-team-name', 'label'),
    dash.dependencies.Input('b-scatter-season-year', 'label'),
    dash.dependencies.Input('b-scatter-qualified', 'value')]
)
def update_scatter_data(data, x_axis, y_axis, team_names, seasons, qualified):
    if data is None:
        return scatter_placeholder, None, None
    else:
        if x_axis is None:
            x_axis = 'Age'
        if y_axis is None:
            y_axis = 'BA'
        df = pd.read_json(data, orient='split').round(3)
        if qualified:
            df1 = df[(df.PA >= 186) & (df.season == 2020)]
            df2 = df[df.PA > 502]
            df = pd.concat([df1,df2])
        # Clean up hover info
        hover_data = {'Name': True, 'season': True, 'Team': False} if seasons and len(seasons) > 1 else {'Name': True, 'Team': False}
        fig = px.scatter(df, x=x_axis, y=y_axis, hover_data=hover_data, trendline='ols', trendline_color_override='black')
        # Configure trendline
        fig.data[1]['line'].update(dash='dash')
        fig.update_xaxes(title=x_axis, type='linear')
        fig.update_yaxes(title=y_axis, type='linear')
        fig.update_layout(font={'size': 18, 'family': 'Segoe UI'}, hovermode='closest')
        
        # Make sure to only have numeric columns as axis options
        axis_options = list(df.select_dtypes(include=[np.number]).columns.values)
        axis_options = [{'label': col, 'value': col} for col in axis_options]

        scatter_title = f'{y_axis} vs. {x_axis} (Pearson Correlation: {df[y_axis].corr(df[x_axis]).round(5)})'

        return dcc.Graph(figure=fig, style={'height': '80vh'}), axis_options, axis_options, scatter_title

