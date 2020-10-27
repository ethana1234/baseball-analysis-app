import sys,requests,sqlite3,json,hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
from lxml import html
from requests.exceptions import HTTPError

sql_max_int = 2147483647
team_codes = [
    'ARI',
    'ATL',
    'BAL',
    'BOS',
    'CHC',
    'CHW',
    'CIN',
    'CLE',
    'COL',
    'DET',
    'HOU',
    'KCR',
    'LAA',
    'LAD',
    'MIA',
    'MIL',
    'MIN',
    'NYM',
    'NYY',
    'OAK',
    'PHI',
    'PIT',
    'SDP',
    'SFG',
    'SEA',
    'STL',
    'TBR',
    'TEX',
    'TOR',
    'WSN'
]
team_id_dict = dict(zip(team_codes, list(range(len(team_codes)))))

def db_setup():
    # Connect to db
    # Setup db connection, conn variable is None if connection unsuccessful
    conn = None
    try:
        # Note that if db file doesn't already exist, one will be made
        # Also be weary of the check_same_thread condition, could cause problems if multiple threads try to access db
        conn = sqlite3.connect('D:/mydata/baseball.db', check_same_thread=False)
    except Exception as e:
        # Don't continue if there's an Exception here
        db_error_cleanup(conn, e)
    return conn

def db_error_cleanup(conn, e):
    # Proper cleanup of db after catching an Exception
    conn.rollback()
    conn.close()
    raise e

def new_db(conn):
    # Drop and recreate tables
    with open('D:/personal/baseball-analysis-app/server/db_scripts/new_tables.sql', 'r') as f:
        script = f.read()
        conn.executescript(script)

    # Populate Teams table
    df = pd.read_csv('D:/personal/baseball-analysis-app/server/db_scripts/team_table.csv')
    df['id'] = df['id'].apply(pd.to_numeric)
    df.set_index('id', inplace=True)
    df.to_sql('Teams', conn, if_exists='append')

    conn.commit()

def clean_batting_data(data, team_code, year):
    #   Rename some of the columns
    data.rename(columns={'Unnamed: 3':'HomeAway',
                        'Thr':'OppStarterThr',
                        'Opp':'opp_id',
                        'Date': 'game_date'}, inplace=True)

    #   Drop place holder rows 
    data.drop(data[data.OBP == 'OBP'].index, inplace=True)

    #   Fix Home/Away column values
    data.replace({'HomeAway': {'@':'A'}}, inplace=True)
    data.HomeAway.fillna('H', inplace=True)

    #   Split result column into multiple columns
    data[['Result', 'RunsAgainst']] = data.Rslt.str.split(',', expand=True)
    data.RunsAgainst = data.RunsAgainst.str.split('-').str[1]

    #   Fix Date column for double headers and made it SQLite compatible
    data.game_date = data.game_date.str.encode('ascii', 'ignore').str.decode('ascii').str.strip()
    data.game_date = data.game_date.str.replace('susp', '')
    data.game_date = data.game_date.str.split('(').str[0] + str(year)
    data.game_date = data.game_date.str.replace(' ', '')
    data.game_date = data.game_date.apply(lambda x: datetime.strptime(x, '%b%d%Y').strftime('%Y-%m-%d'))
    data['season'] = year

    #   Generate unique game id for each game and make it the index (home/away independent)
    game_ids = [data.game_date.iloc[i] + ((data.opp_id.iloc[i] + data.RunsAgainst.iloc[i] + team_code + data.R.iloc[i]) if data.HomeAway.iloc[i] == 'H' else (team_code + data.R.iloc[i] + data.opp_id.iloc[i] + data.RunsAgainst.iloc[i])) for i in range(len(data.index))]
    game_ids = [int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % sql_max_int for s in game_ids]
    data['game_id'] = game_ids

    # Add team ids
    data['team_id'] = team_id_dict[team_code]
    data.opp_id = data.opp_id.apply(lambda x: team_id_dict[x])

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm', '#', 'Opp. Starter (GmeSc)'], inplace=True)
    data = data[['game_id', 'team_id', 'opp_id', 'game_date', 'season', 'HomeAway', 'OppStarterThr', 'Result', 'RunsAgainst', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB',
                'IBB', 'SO', 'HBP', 'SH', 'SF', 'ROE', 'GDP', 'SB', 'CS', 'LOB', 'BA', 'OBP', 'SLG', 'OPS']]
                
    #   Convert numeric columns to numeric types
    data = data.copy()
    data.loc[:, 'RunsAgainst':] = data.loc[:, 'RunsAgainst':].apply(pd.to_numeric)

    data.set_index(['game_id','team_id'], inplace=True)

    return data

def clean_pitching_data(data, team_code, year):
    #   Rename some of the columns
    data.rename(columns={'Unnamed: 3':'HomeAway',
                        '#': 'PitchersUsed',
                        'Pit': 'Pitches',
                        'Opp': 'opp_id',
                        'Str': 'Strikes',
                        'Date': 'game_date'}, inplace=True)

    #   Drop place holder rows 
    data.drop(data[data.ERA == 'ERA'].index, inplace=True)

    #   Fix Home/Away column values
    data.replace({'HomeAway': {'@':'A'}}, inplace=True)
    data.HomeAway.fillna('H', inplace=True)

    #   Split result column into multiple columns
    data[['Result', 'RunsFor']] = data.Rslt.str.split(',', expand=True)
    data.RunsFor = data.RunsFor.str.split('-').str[0]

    #   Fix Date column for double headers and made it SQLite compatible
    data.game_date = data.game_date.str.encode('ascii', 'ignore').str.decode('ascii').str.strip()
    data.game_date = data.game_date.str.replace('susp', '')
    data.game_date = data.game_date.str.split('(').str[0] + str(year)
    data.game_date = data.game_date.str.replace(' ', '')
    data.game_date = data.game_date.apply(lambda x: datetime.strptime(x, '%b%d%Y').strftime('%Y-%m-%d'))
    data['season'] = year

    #   Generate unique game id for each game (home/away independent) and make it the index
    game_ids = [data.game_date.iloc[i] + ((data.opp_id.iloc[i] + data.R.iloc[i] + team_code + data.RunsFor.iloc[i]) if data.HomeAway.iloc[i] == 'H' else (team_code + data.RunsFor.iloc[i] + data.opp_id.iloc[i] + data.R.iloc[i])) for i in range(len(data.index))]
    game_ids = [int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % sql_max_int for s in game_ids]
    data['game_id'] = game_ids

    # Add team ids
    data['team_id'] = team_id_dict[team_code]
    data.opp_id = data.opp_id.apply(lambda x: team_id_dict[x])

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm', 'Umpire', 'Pitchers Used (Rest-GameScore-Dec)'], inplace=True)
    data = data[['game_id', 'team_id', 'opp_id', 'game_date', 'season', 'HomeAway', 'Result', 'RunsFor', 'H', 'R', 'ER', 'UER', 'BB', 'SO', 'HR', 'HBP', 'BF', 'Pitches', 'Strikes', 'IR',
            'IS', 'SB', 'CS', 'AB', '2B', '3B', 'IBB', 'SH', 'SF', 'ROE', 'GDP', 'PitchersUsed', 'IP', 'ERA']]
                
    #   Convert numeric columns to numeric types
    data.loc[:, 'RunsFor':] = data.loc[:, 'RunsFor':].apply(pd.to_numeric)

    data.set_index(['game_id','team_id'], inplace=True)

    return data

def insert_team_data(conn, team_code, year):
    # Retrieve html from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=b&year={year}'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err
    
    # Pull important data from xml tree
    tree = html.fromstring(r.content)
    wins,losses = tree.xpath('//div/div/div/div[contains(@data-template, \'Partials/Teams/Summary\')]/p/text()[contains(.,\'-\')]')[0].split()[0].split('-')
    losses = losses[:-1]

    # SQLite insert team
    query = 'INSERT INTO TeamSeason (team_id, season, wins, losses) VALUES (?,?,?,?)'
    try:
        conn.execute(query, (team_id_dict[team_code], year, wins, losses))
    #except sqlite3.IntegrityError:
        #return 'Team Season exists'
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_batting_team_data(conn, team_code, year):
    # Retrieve team batting data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=b&year={year}'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err

    # Retrieve Batting Table from XML page and put into a DataFrame
    soup = BeautifulSoup(r.content, "lxml")
    table = soup.find('table', attrs=dict(id='team_batting_gamelogs'))
    data = pd.read_html(str(table))[0]

    clean_data = clean_batting_data(data, team_code, year)

    try:
        clean_data.to_sql('TeamBattingGame', conn, if_exists='append')
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_pitching_team_data(conn, team_code, year):
    # Retrieve team batting data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=p&year={year}'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err

    # Retrieve Batting Table from XML page and put into a DataFrame
    soup = BeautifulSoup(r.content, "lxml")
    table = soup.find('table', attrs=dict(id='team_pitching_gamelogs'))
    data = pd.read_html(str(table))[0]

    clean_data = clean_pitching_data(data, team_code, year)

    try:
        clean_data.to_sql('TeamPitchingGame', conn, if_exists='append')
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True



if __name__=='__main__':
    conn = db_setup()
    new_db(conn)
    for team in team_codes:
        for year in [2020,2019,2018]:
            print(team, year)
            print('\t', insert_team_data(conn, team, year))
            print('\t', insert_batting_team_data(conn, team, year))
            print('\t', insert_pitching_team_data(conn, team, year))

    conn.close()
