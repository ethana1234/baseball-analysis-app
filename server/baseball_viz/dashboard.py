import dash
from flask import jsonify, abort, request, send_from_directory, Response, render_template
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import sys,requests,json,hashlib,os
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from datetime import datetime


def create_dashboard(dash_app):
    # Create Dash visualization
    all_data = []
    years = ['2020','2019','2018','2017']
    for year in years:
        url = f'https://www.baseball-reference.com/teams/PHI/{year}-batting.shtml'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'lxml')
        table = soup.find('table', attrs=dict(id='team_batting'))
        data = pd.read_html(str(table))[0]
        data.drop(data[data['Name'] == 'Name'].index, inplace=True)
        data = data[data['Rk'].notna()]
        data.set_index('Rk', inplace=True)
        data['Name'] = data['Name'].str.replace(r'[^a-zA-Z\s]', '')
        data.drop(data[data['Pos'] == 'P'].index, inplace=True)
        data['Year'] = year
        data.loc[:, 'Age':'Year'] = data.loc[:, 'Age':'Year'].apply(pd.to_numeric)
        all_data.append(data)
    df = pd.concat(all_data)
    stats = df.columns[5:12]

    controls = dbc.Row([
        dbc.Col(html.Div(dbc.FormGroup([
            dbc.Label('X variable'),
            dcc.Dropdown(
                id='crossfilter-xaxis-column',
                options=[{'label': i, 'value': i} for i in stats],
                value='AB'
            )
        ]))),
        dbc.Col(html.Div(dbc.FormGroup([
            dbc.Label('Y variable'),
            dcc.Dropdown(
                id='crossfilter-yaxis-column',
                options=[{'label': i, 'value': i} for i in stats],
                value='HR'
            )
        ])))
    ])

    dash_app.layout = dbc.Container([
        html.H1('Relational Player Graph'),
        html.Hr(),
        html.Div(controls),

        html.Div([
            dcc.Graph(
                id='crossfilter-indicator-scatter',
                hoverData={'points': [{'customdata': 'Bryce Harper'}]}
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
        
        html.Div([
            dcc.Graph(id='x-time-series'),
            dcc.Graph(id='y-time-series'),
        ], style={'display': 'inline-block', 'width': '49%'}),

        html.Div(dcc.Slider(
            id='crossfilter-year--slider',
            min=df['Year'].min(),
            max=df['Year'].max(),
            value=df['Year'].max(),
            marks={year: year for year in years},
            step=None
        ), style={'width': '49%', 'padding': '0px 20px 20px 20px'})
    ])

    # Create routes for Dash app
    app = dash_app.server
    from . import routes

    # Initialize callbacks after app is loaded
    init_callbacks(dash_app, df)

    return dash_app.server

def init_callbacks(dash_app, df):
    @dash_app.callback(
        dash.dependencies.Output('crossfilter-indicator-scatter', 'figure'),
        [dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
        dash.dependencies.Input('crossfilter-yaxis-column', 'value'),
        dash.dependencies.Input('crossfilter-year--slider', 'value')])
    def update_graph(xaxis_column_name, yaxis_column_name, year_value):
        dff = df[df['Year'] == year_value]

        fig = px.scatter(x=dff[xaxis_column_name],
                y=dff[yaxis_column_name],
                hover_name=dff['Name']
                )

        fig.update_traces(customdata=dff['Name'])

        fig.update_xaxes(title=xaxis_column_name, type='linear')

        fig.update_yaxes(title=yaxis_column_name, type='linear')

        fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

        return fig


    def create_time_series(dff, title, xaxis_column_name):

        fig = px.scatter(dff, x='Year', y=xaxis_column_name)

        fig.update_traces(mode='lines+markers')

        fig.update_xaxes(showgrid=False, type='category', categoryorder='category ascending')

        fig.update_yaxes(type='linear')

        fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                        xref='paper', yref='paper', showarrow=False, align='left',
                        bgcolor='rgba(255, 255, 255, 0.5)', text=title)

        fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

        return fig


    @dash_app.callback(
        dash.dependencies.Output('x-time-series', 'figure'),
        [dash.dependencies.Input('crossfilter-indicator-scatter', 'hoverData'),
        dash.dependencies.Input('crossfilter-xaxis-column', 'value')])
    def update_y_timeseries(hoverData, xaxis_column_name):
        player_name = hoverData['points'][0]['customdata']
        dff = df[df['Name'] == player_name]
        title = f'<b>{player_name}</b><br>{xaxis_column_name}'
        return create_time_series(dff, title, xaxis_column_name)


    @dash_app.callback(
        dash.dependencies.Output('y-time-series', 'figure'),
        [dash.dependencies.Input('crossfilter-indicator-scatter', 'hoverData'),
        dash.dependencies.Input('crossfilter-yaxis-column', 'value')])
    def update_x_timeseries(hoverData, yaxis_column_name):
        player_name = hoverData['points'][0]['customdata']
        dff = df[df['Name'] == player_name]
        return create_time_series(dff, yaxis_column_name, yaxis_column_name)

