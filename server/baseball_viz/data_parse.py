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
    except sqlite3.IntegrityError:
        return f'Team Season exists: {team_code} {year}' 
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_batting_game_data(conn, team_code, year):
    team_id = team_id_dict[team_code]

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
    data['team_id'] = team_id
    data.opp_id = data.opp_id.apply(lambda x: team_id_dict[x])

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm', '#', 'Opp. Starter (GmeSc)'], inplace=True)
    data = data[['game_id', 'team_id', 'opp_id', 'game_date', 'season', 'HomeAway', 'OppStarterThr', 'Result', 'RunsAgainst', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB',
                'IBB', 'SO', 'HBP', 'SH', 'SF', 'ROE', 'GDP', 'SB', 'CS', 'LOB', 'BA', 'OBP', 'SLG', 'OPS']]
                
    #   Convert numeric columns to numeric types
    data = data.copy()
    data.loc[:, 'RunsAgainst':] = data.loc[:, 'RunsAgainst':].apply(pd.to_numeric)

    data.set_index(['game_id','team_id'], inplace=True)

    try:
        data.to_sql('TeamBattingGame', conn, if_exists='append')
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_pitching_game_data(conn, team_code, year):
    team_id = team_id_dict[team_code]

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
    data['team_id'] = team_id
    data.opp_id = data.opp_id.apply(lambda x: team_id_dict[x])

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm', 'Umpire', 'Pitchers Used (Rest-GameScore-Dec)'], inplace=True)
    data = data[['game_id', 'team_id', 'opp_id', 'game_date', 'season', 'HomeAway', 'Result', 'RunsFor', 'H', 'R', 'ER', 'UER', 'BB', 'SO', 'HR', 'HBP', 'BF', 'Pitches', 'Strikes', 'IR',
            'IS', 'SB', 'CS', 'AB', '2B', '3B', 'IBB', 'SH', 'SF', 'ROE', 'GDP', 'PitchersUsed', 'IP', 'ERA']]
                
    #   Convert numeric columns to numeric types
    data.loc[:, 'RunsFor':] = data.loc[:, 'RunsFor':].apply(pd.to_numeric)

    data.set_index(['game_id','team_id'], inplace=True)

    try:
        data.to_sql('TeamPitchingGame', conn, if_exists='append')
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_batting_season_data(conn, team_code, year):
    team_id = team_id_dict[team_code]

    # Retrieve team batting data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/{team_code}/{year}-batting.shtml'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err

    # Retrieve Batting Table from XML page and put into a DataFrame
    soup = BeautifulSoup(r.content, "lxml")
    table = soup.find('table', attrs=dict(id='team_batting'))
    data = pd.read_html(str(table))[0]

    #   Get team's overall stats for the season
    team_batting_data = data.loc[data['Name'] == 'Team Totals'].copy()
    team_batting_data.drop(columns=['Rk', 'Pos', 'Name', 'OPS+'], inplace=True)
    team_batting_data = list(pd.to_numeric(team_batting_data.iloc[0]).round(3))

    #   Drop place holder rows 
    data.drop(data[data.OBP == 'OBP'].index, inplace=True)
    data.dropna(axis=0, subset=['Rk'], inplace=True)

    #   Remove players with no at bats
    data.fillna('0', inplace=True)
    data = data[data.AB != '0']

    #   Add player ids
    player_elements = table.findAll('td', attrs={'data-stat':'player'})
    player_ids = {}
    for row in player_elements:
        player_id = row.get('data-append-csv', None)
        if player_id is None:
            continue
        player_ids[row.get_text()] = player_id
    data.insert(0, 'player_id', data.Name.map(player_ids))
    data.insert(1, 'season', year)
    data.insert(2, 'team_id', team_id)

    #   Create new df to insert in Players table
    players = data[['player_id', 'Name', 'Pos']].copy()
    players.loc[players.Name.str.contains('\*'), 'Handedness'] = 'L'
    players.loc[players.Name.str.contains('\#'), 'Handedness'] = 'S'
    players.Handedness.fillna('R', inplace=True)
    players.Name = players.Name.str.rstrip('*#')
    players.set_index('player_id', inplace=True)

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rk', 'Name', 'Pos', 'OPS+'], inplace=True)
                
    #   Convert numeric columns to numeric types
    data.loc['Age':] = data.loc['Age':].apply(pd.to_numeric)

    data.set_index(['player_id', 'season', 'team_id'], inplace=True)

    # Insert players into Players table if they're not already there
    query = 'INSERT INTO Batters (id, Name, Pos, Handedness) VALUES (?,?,?,?)'
    for i,row in players.iterrows():
        try:
            conn.execute(query, (i, *row))
        except sqlite3.IntegrityError:
            print(f'Player already inserted: {row[0]}')

    try:
        # Insert player and team's season batting data
        data.to_sql('PlayerBattingSeason', conn, if_exists='append')
        query = 'INSERT INTO TeamBattingSeason (team_id, season, Age, G, PA, AB, R, H, "2B", "3B", HR, RBI, SB, CS, BB, SO, BA, OBP, SLG, OPS, TB, GDP, HBP, SH, SF, IBB) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        conn.execute(query, (team_id, year, *team_batting_data))
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_pitching_season_data(conn, team_code, year):
    team_id = team_id_dict[team_code]

    # Retrieve team batting data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/{team_code}/{year}-pitching.shtml'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err

    # Retrieve Batting Table from XML page and put into a DataFrame
    soup = BeautifulSoup(r.content, "lxml")
    table = soup.find('table', attrs=dict(id='team_pitching'))
    data = pd.read_html(str(table))[0]

    #   Get team's overall stats for the season
    team_pitching_data = data.loc[data['Name'] == 'Team Totals'].copy()
    team_pitching_data.drop(columns=['Rk', 'Pos', 'Name', 'SO/W', 'ERA+', 'W', 'L', 'W-L%'], inplace=True)
    team_pitching_data = list(pd.to_numeric(team_pitching_data.iloc[0]).round(3))

    #   Rename some of the columns
    data.rename(columns={'W':'wins',
                        'L':'losses'}, inplace=True)

    #   Drop place holder rows 
    data.drop(data[data.ERA == 'ERA'].index, inplace=True)
    data.dropna(axis=0, subset=['Rk'], inplace=True)

    #   Fill NaN win-loss %
    data.fillna(.000, inplace=True)

    #   Add player ids
    player_elements = table.findAll('td', attrs={'data-stat':'player'})
    player_ids = {}
    for row in player_elements:
        player_id = row.get('data-append-csv', None)
        if player_id is None:
            continue
        player_ids[row.get_text()] = player_id
    data.insert(0, 'player_id', data.Name.map(player_ids))
    data.insert(1, 'season', year)
    data.insert(2, 'team_id', team_id)

    #   Create new df to insert in Players table
    players = data[['player_id', 'Name']].copy()
    players.loc[players.Name.str.contains('\*'), 'Handedness'] = 'L'
    players.loc[players.Name.str.contains('\#'), 'Handedness'] = 'S'
    players.Handedness.fillna('R', inplace=True)
    players.Name = players.Name.str.rstrip('*#')
    players.set_index('player_id', inplace=True)

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rk', 'Name', 'Pos', 'W-L%', 'SO/W', 'ERA+'], inplace=True)
                
    #   Convert numeric columns to numeric types
    data.loc['Age':] = data.loc['Age':].apply(pd.to_numeric)

    data.set_index(['player_id', 'season', 'team_id'], inplace=True)

    # Insert players into Players table if they're not already there
    query = 'INSERT INTO Pitchers (id, Name, Handedness) VALUES (?,?,?)'
    for i,row in players.iterrows():
        try:
            conn.execute(query, (i, *row))
        except sqlite3.IntegrityError:
            print(f'Player already inserted: {row[0]}')

    try:
        # Insert player and team's season pitching data
        data.to_sql('PlayerPitchingSeason', conn, if_exists='append')
        query = 'INSERT INTO TeamPitchingSeason (team_id, season, Age, ERA, G, GS, GF, CG, SHO, SV, IP, H, R, ER, HR, BB, IBB, SO, HBP, BK, WP, BF, FIP, WHIP, H9, HR9, BB9, SO9) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        conn.execute(query, (team_id, year, *team_pitching_data))
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
            print('\t', insert_batting_game_data(conn, team, year))
            print('\t', insert_pitching_game_data(conn, team, year))
            print('\t', insert_batting_season_data(conn, team, year))
            print('\t', insert_pitching_season_data(conn, team, year))
    conn.close()
