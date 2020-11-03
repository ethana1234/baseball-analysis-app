import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm

import pandas as pd
import numpy as np

# This file has general creation of plotly graphs

def build_scatter(df, x_axis, y_axis, seasons):
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

    scatter_title = f'{y_axis} vs. {x_axis} (Pearson Correlation: {df[y_axis].corr(df[x_axis]).round(5)})'

    return dcc.Graph(figure=fig, style={'height': '80vh'}), axis_options, axis_options, scatter_title

def build_time_series(df, y_axis, team_ids, hover_template):
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
        yaxis=dict(title=y_axis),
    )
    multiple_teams = (team_ids is not None) and (len(team_ids) > 1)
    fig.update_traces(hovertemplate=hover_template, showlegend=multiple_teams)

    # Show comparison to season average (only if there's one team)
    if not multiple_teams:
        fig.add_trace(
            go.Scatter(
                mode='markers',
                x=[df.game_date.min(), df.game_date.max()],
                y=[df[y_axis].mean(), df[y_axis].mean()],
                hoverinfo='skip',
                showlegend=False,
                marker=dict(opacity=0),
                fill='tonexty',
                fillcolor='#C0C5FE'
            )
        )

    # Make sure to only have numeric columns as axis options
    axis_options = list(df.select_dtypes(include=[np.number]).columns.values)
    axis_options = [{'label': col, 'value': col} for col in axis_options]
    ts_title = f'Time Series for {y_axis}'
    return dcc.Graph(figure=fig, style={'height': '80vh'}), axis_options, ts_title
