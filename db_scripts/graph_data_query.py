import pandas as pd
import numpy as np
from db_scripts.db_connect import db_setup,db_error_cleanup

# This file has general interaction with the SQLite database, and will return DataFrames from the queries
# Any DataFrame cleanup should be done in the page's update_dataframe function
# table_type is either 'b' or 'p'

def make_query(query, team_ids, years):
    with db_setup() as conn:
        df = pd.read_sql_query(query, conn, params=[*team_ids, *years], coerce_float=True)
    return df

def get_players(team_ids, years, table_type):
    # From Player season table
    if table_type == 'b':
        query = f'''
            SELECT b.Name, b.Pos, b.Handedness, t.team_code Team, pbs.*
            FROM Teams t JOIN PlayerBattingSeason pbs
                ON t.id=pbs.team_id
            JOIN Batters b
                ON pbs.player_id=b.id
            WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
                AND pbs.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    else:
        query = f'''
            SELECT p.Name, p.Handedness, t.team_code Team, pps.*
            FROM Teams t JOIN PlayerPitchingSeason pps
                ON t.id=pps.team_id
            JOIN Pitchers p
                ON pps.player_id=p.id
            WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
                AND pps.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    return make_query(query, team_ids, years)

def get_team_season(team_ids, years, table_type):
    # Team season table
    if table_type == 'b':
        query = f'''
            SELECT t.Name, (ts.wins || '-' || ts.losses) as Record, tbs.*
            FROM Teams t JOIN TeamBattingSeason tbs
                ON t.id=tbs.team_id
            JOIN TeamSeason ts
                ON t.id=ts.team_id
                    AND ts.season=tbs.season
            WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
                AND tbs.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    else:
        query = f'''
            SELECT t.Name, (ts.wins || '-' || ts.losses) as Record, tps.*
            FROM Teams t JOIN TeamPitchingSeason tps
                ON t.id=tps.team_id
            JOIN TeamSeason ts
                ON t.id=ts.team_id
                    AND ts.season=tps.season
            WHERE t.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
                AND tps.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    
    return make_query(query, team_ids, years)

def get_gamelogs(team_ids, years, table_type):
    # From gamelogs table
    if table_type == 'b':
        query = f'''
            SELECT t1.team_code Team, t1.team_code || CASE tbg.HomeAway WHEN 'H' THEN ' vs. ' ELSE ' @ ' END || t2.team_code Game, tbg.R || '-' || tbg.RunsAgainst Score, tbg.*
            FROM Teams t1 JOIN TeamBattingGame tbg
                ON t1.id=tbg.team_id
            JOIN Teams t2
                ON t2.id=tbg.opp_id
            WHERE t1.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
                AND tbg.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    else:
        query = f'''
            SELECT t1.team_code Team, t1.team_code || CASE tpg.HomeAway WHEN 'H' THEN ' vs. ' ELSE ' @ ' END || t2.team_code Game, tpg.RunsFor || '-' || tpg.R Score, tpg.*
            FROM Teams t1 JOIN TeamPitchingGame tpg
                ON t1.id=tpg.team_id
            JOIN Teams t2
                ON t2.id=tpg.opp_id
            WHERE t1.id {'IN (' + ','.join(['?' for _ in team_ids]) + ')' if len(team_ids)>1 else '=?'}
                AND tpg.season {'IN (' + ','.join(['?' for _ in years]) + ')' if len(years)>1 else '=?'}'''
    
    return make_query(query, team_ids, years)


