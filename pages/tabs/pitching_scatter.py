import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
import pandas as pd
import numpy as np

from app import app
from db_scripts.db_connect import db_setup,db_error_cleanup
from data_insert import team_id_dict

def get_pitchers(team_ids, years):
    conn = db_setup()
    query = f'''
        SELECT p.Name, p.Handedness, t.team_code Team, pps.*
        FROM Teams t JOIN PlayerPitchingSeason pps
            ON t.id=pps.team_id
        JOIN Pitchers p
            ON pps.player_id=p.id
        WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
            AND pps.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True)
    conn.close()

    df.drop(columns=['player_id', 'team_id'], inplace=True)

    return df

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
    dash.dependencies.Output('p-scatter-save', 'children'),
    [dash.dependencies.Input('p-scatter-team-name', 'value'),
    dash.dependencies.Input('p-scatter-season-year', 'value'),]
)
def update_dataframe(team_ids, years):
    if team_ids is None or not team_ids:
        team_ids = [20]
    if years is None or not years:
        years = [2020]
    df = get_pitchers(team_ids, years)
    
    return df.to_json(orient='split')

@app.callback(
    [dash.dependencies.Output('p-scatter-result', 'children'),
    dash.dependencies.Output('p-scatter-x', 'options'),
    dash.dependencies.Output('p-scatter-y', 'options'),
    dash.dependencies.Output('p-scatter-label', 'children')],
    [dash.dependencies.Input('p-scatter-save', 'children'),
    dash.dependencies.Input('p-scatter-x', 'value'),
    dash.dependencies.Input('p-scatter-y', 'value'),
    dash.dependencies.Input('p-scatter-season-year', 'value'),
    dash.dependencies.Input('p-scatter-qualified', 'value')]
)
def update_scatter_data(data, x_axis, y_axis, seasons, qualified):
    if data is None:
        return scatter_placeholder, None, None
    else:
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
        # Make year categorical
        df['season'] = df.season.astype(str)
        
        fig = px.scatter(df, x=x_axis, y=y_axis, color='season')
        # Clean up hover info
        season_len = (seasons is not None) and (len(seasons) > 1)
        hovertemplate = 'Player: %{customdata[0]}<br>Season: %{customdata[1]}<extra></extra>' if season_len else 'Player: %{customdata[0]}<extra></extra>'
        fig.update_traces(
            customdata=np.stack((df.Name, df.season), axis=-1),
            hovertemplate=hovertemplate,
            showlegend=season_len
        )

        # Configure trendline
        regline = sm.OLS(df[y_axis], sm.add_constant(df[x_axis])).fit().fittedvalues
        # add linear regression line for whole sample
        fig.add_traces(
            go.Scatter(
                x=df[x_axis],
                y=regline,
                mode = 'lines',
                marker_color='black',
                opacity=.25,
                hoverinfo='skip',
                showlegend=False,
            )
        )

        fig.update_layout(
            font=dict(
                size=18,
                family='Segoe UI'
            ),
            hovermode='closest',
            xaxis=dict(
                title=x_axis,
                type='linear',
                showspikes=True,
                spikemode='across',
                spikethickness=2,
                spikedash='dot',
                spikecolor='grey'
            ),
            yaxis=dict(
                title=y_axis,
                type='linear',
                showspikes=True,
                spikemode='across',
                spikethickness=2,
                spikedash='dot',
                spikecolor='grey'
            )
        )
        
        
        # Make sure to only have numeric columns as axis options
        axis_options = list(df.select_dtypes(include=[np.number]).columns.values)
        axis_options = [{'label': col, 'value': col} for col in axis_options]

        # Make sure to only have numeric columns as axis options
        axis_options = list(df.select_dtypes(include=[np.number]).columns.values)
        axis_options = [{'label': col, 'value': col} for col in axis_options]

        scatter_title = f'{y_axis} vs. {x_axis} (Pearson Correlation: {df[y_axis].corr(df[x_axis]).round(5)})'

        return dcc.Graph(figure=fig, style={'height': '80vh'}), axis_options, axis_options, scatter_title

