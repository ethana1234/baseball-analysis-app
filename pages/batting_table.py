import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd

from app import app
import data_parse

def get_batters(max_rows=10):
    f

def generate_table(max_rows=10):
    dataframe = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')
    dataframe.rename(columns={'Unnamed: 0':'#'}, inplace=True)
    return dbc.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ],
    bordered=True)

layout = html.Div(children=[
    html.H4(children='US Agriculture Exports (2011)'),
    generate_table()
])
