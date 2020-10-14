import sys,requests,sqlite3,json,hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
from lxml import html
from requests.exceptions import HTTPError

sql_max_int = 2147483647

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
    conn.cursor().close()
    conn.close()
    raise e

def create_table(conn, query):
    try:
        conn.cursor().execute(query)
        conn.commit()
    except Exception as e:
        db_error_cleanup(conn, e)

def create_baseball_tables(conn):
    queries = []
    # Setup the tables on the db if not done already
    queries.append('''
    CREATE TABLE IF NOT EXISTS Team (
        id integer PRIMARY KEY,
        name string NOT NULL,
        team_code string NOT NULL,
        league string NOT NULL,
        division string NOT NULL,
        wins integer DEFAULT 0,
        losses integer DEFAULT 0
    )''')
    queries.append('''
    CREATE TABLE IF NOT EXISTS BattingGame (
        game_id integer NOT NULL,
        team_id integer NOT NULL,
        Date string,
        team_code string,
        HomeAway string,
        Opp string,
        Result string,
        RunsAgainst integer,
        PA integer,
        AB integer,
        R integer,
        H integer,
        "2B" integer,
        "3B" integer,
        HR integer,
        RBI integer,
        BB integer,
        IBB integer,
        SO integer,
        HBP integer,
        SH integer,
        SF integer,
        ROE integer,
        GDP integer,
        SB integer,
        CS integer,
        LOB integer,
        PlayersUsed integer,
        BA real,
        OBP real,
        SLG real,
        OPS real,
        OppStarterThr string,
        PRIMARY KEY (game_id, team_id),
        FOREIGN KEY(team_id) REFERENCES Team(id)
    )''')
    queries.append('''
    CREATE TABLE IF NOT EXISTS PitchingGame (
        game_id integer NOT NULL,
        team_id integer NOT NULL,
        Date string,
        team_code string,
        HomeAway string,
        Opp string,
        Result string,
        RunsFor integer,
        H integer,
        R integer,
        ER integer,
        UER integer,
        BB integer,
        SO integer,
        HR integer,
        HBP integer,
        BF integer,
        Pitches integer,
        Strikes integer,
        IR integer,
        "IS" integer,
        SB integer,
        CS integer,
        AB integer,
        "2B" integer,
        "3B" integer,
        IBB integer,
        SH integer,
        SF integer,
        ROE integer,
        GDP integer,
        PitchersUsed integer,
        IP real,
        ERA real,
        Umpire string,
        StartingPitcher string,
        DecidingPitcher string,
        PRIMARY KEY (game_id, team_id),
        FOREIGN KEY(team_id) REFERENCES Team(id)
    )''')

    for query in queries:
        create_table(conn, query)

def clean_batting_data(data, team_code):
    #   Rename some of the columns
    data.rename(columns={'Unnamed: 3':'HomeAway', 'Thr':'OppStarterThr', '#':'PlayersUsed'}, inplace=True)

    #   Drop place holder rows 
    data.drop(data[data['OBP'] == 'OBP'].index, inplace=True)

    #   Fix Home/Away column values
    data.replace({'HomeAway': {'@':'A'}}, inplace=True)
    data['HomeAway'].fillna('H', inplace=True)

    #   Split result column into multiple columns
    data[['Result', 'RunsAgainst']] = data['Rslt'].str.split(',', expand=True)
    data['RunsAgainst'] = data['RunsAgainst'].str.split('-').str[1]

    #   Fix Date column for double headers and made it SQLite compatible
    data['Date'] = data['Date'].str.split('(').str[0] + ' 2020'
    data['Date'] = data['Date'].apply(lambda x: datetime.strptime(x, '%b %d %Y').strftime('%Y-%m-%d'))

    #   Generate unique game id for each game and make it the index (home/away independent)
    game_ids = [data['Date'].iloc[i] + ((data['Opp'].iloc[i] + data['RunsAgainst'].iloc[i] + team_code + data['R'].iloc[i]) if data['HomeAway'].iloc[i] == 'H' else (team_code + data['R'].iloc[i] + data['Opp'].iloc[i] + data['RunsAgainst'].iloc[i])) for i in range(len(data.index))]
    game_ids = [int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % sql_max_int for s in game_ids]
    data['game_id'] = game_ids
    data.set_index('game_id', inplace=True)

    # Add team id based on 3 letter team code
    team_ids = [sum([i*j for i,j in zip([1 + ord(team_code[1]),2,3],[ord(char) for char in team_code])]) for _ in range(len(data.index))]
    data['team_id'] = team_ids
    data['team_code'] = team_code

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm', 'Opp. Starter (GmeSc)'], inplace=True)
    data = data[['team_id', 'Date', 'team_code', 'HomeAway', 'Opp', 'Result', 'RunsAgainst', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB',
                'IBB', 'SO', 'HBP', 'SH', 'SF', 'ROE', 'GDP', 'SB', 'CS', 'LOB', 'PlayersUsed', 'BA', 'OBP', 'SLG', 'OPS', 'OppStarterThr']]
                
    #   Convert numeric columns to numeric types
    data.loc[:, 'RunsAgainst':'PlayersUsed'] = data.loc[:, 'RunsAgainst':'PlayersUsed'].apply(pd.to_numeric)
    data.loc[:, 'BA':'OPS'] = data.loc[:, 'BA':'OPS'].apply(pd.to_numeric)

    return data

def clean_pitching_data(data, team_code):
    #   Rename some of the columns
    data.rename(columns={'Unnamed: 3':'HomeAway',
                        'Pitchers Used (Rest-GameScore-Dec)':'StartingPitcher',
                        '#':'PitchersUsed',
                        'Pit': 'Pitches',
                        'Str': 'Strikes'}, inplace=True)

    #   Drop place holder rows 
    data.drop(data[data['ERA'] == 'ERA'].index, inplace=True)

    #   Fix Home/Away column values
    data.replace({'HomeAway': {'@':'A'}}, inplace=True)
    data['HomeAway'].fillna('H', inplace=True)

    #   Split result column into multiple columns
    data[['Result', 'RunsFor']] = data['Rslt'].str.split(',', expand=True)
    data['RunsFor'] = data['RunsFor'].str.split('-').str[0]

    #   Fix Date column for double headers and made it SQLite compatible
    data['Date'] = data['Date'].str.split('(').str[0] + ' 2020'
    data['Date'] = data['Date'].apply(lambda x: datetime.strptime(x, '%b %d %Y').strftime('%Y-%m-%d'))

    #   Pull both starting pitcher and pitcher who got the decision
    all_pitchers = [row.split(',') for row in data['StartingPitcher']]
    data['DecidingPitcher'] = [next(string for string in row if 'W' in string or 'L' in string).split()[0] for row in all_pitchers]
    data['StartingPitcher'] = [row[0].split()[0] for row in all_pitchers]

    #   Generate unique game id for each game (home/away independent) and make it the index
    game_ids = [data['Date'].iloc[i] + ((data['Opp'].iloc[i] + data['R'].iloc[i] + team_code + data['RunsFor'].iloc[i]) if data['HomeAway'].iloc[i] == 'H' else (team_code + data['RunsFor'].iloc[i] + data['Opp'].iloc[i] + data['R'].iloc[i])) for i in range(len(data.index))]
    game_ids = [int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % sql_max_int for s in game_ids]
    data['game_id'] = game_ids
    data.set_index('game_id', inplace=True)

    # Add team id based on 3 letter team code
    team_ids = [sum([i*j for i,j in zip([1 + ord(team_code[1]),2,3],[ord(char) for char in team_code])]) for _ in range(len(data.index))]
    data['team_id'] = team_ids
    data['team_code'] = team_code

    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm'], inplace=True)
    data = data[['team_id', 'Date', 'team_code', 'HomeAway', 'Opp', 'Result', 'RunsFor', 'H', 'R', 'ER', 'UER', 'BB', 'SO', 'HR', 'HBP', 'BF', 'Pitches', 'Strikes', 'IR',
            'IS', 'SB', 'CS', 'AB', '2B', '3B', 'IBB', 'SH', 'SF', 'ROE', 'GDP', 'PitchersUsed', 'IP', 'ERA', 'Umpire', 'StartingPitcher', 'DecidingPitcher']]
                
    #   Convert numeric columns to numeric types
    data.loc[:, 'RunsFor':'PitchersUsed'] = data.loc[:, 'RunsFor':'PitchersUsed'].apply(pd.to_numeric)
    data.loc[:, 'IP':'ERA'] = data.loc[:, 'IP':'ERA'].apply(pd.to_numeric)

    return data

def insert_team_data(conn, team_code):
    # Retrieve html from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=b&year=2020'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err
    
    # Pull important data from xml tree
    tree = html.fromstring(r.content)
    league,division = tree.xpath('//div/div/div/div[contains(@data-template, \'Partials/Teams/Summary\')]/p[strong[contains(text(), \'Record\')]]/a/text()')[0].split('_')
    full_name = tree.xpath('//div/div/div/div[contains(@data-template, \'Partials/Teams/Summary\')]/h1/span/text()')[1]
    wins,losses = tree.xpath('//div/div/div/div[contains(@data-template, \'Partials/Teams/Summary\')]/p/text()[contains(.,\'-\')]')[0].split()[0].split('-')
    losses = losses[:-1]

    # SQLite insert team
    team_id = sum([i*j for i,j in zip([1 + ord(team_code[1]),2,3],[ord(char) for char in team_code])])
    query = 'INSERT INTO Team (id, name, team_code, league, division, wins, losses) VALUES (?,?,?,?,?,?,?)'
    try:
        conn.cursor().execute(query, (team_id, full_name, team_code, league, division, wins, losses))
    except sqlite3.IntegrityError:
        return 'Team exists'
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_batting_team_data(conn, team_code):
    # Retrieve team batting data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=b&year=2020'
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

    clean_data = clean_batting_data(data, team_code)

    try:
        clean_data.to_sql('BattingGame', conn, if_exists='append')
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True

def insert_pitching_team_data(conn, team_code):
    # Retrieve team batting data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=p&year=2020'
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

    clean_data = clean_pitching_data(data, team_code)

    try:
        clean_data.to_sql('PitchingGame', conn, if_exists='append')
    except sqlite3.IntegrityError:
        return True
    except Exception as e:
        db_error_cleanup(conn, e)
        return False
    return True



if __name__=='__main__':
    conn = db_setup()
    create_baseball_tables(conn)
    all_team_codes = [
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
    for team in all_team_codes:
        print(team)
        print('\t', insert_team_data(conn, team))
        print('\t', insert_batting_team_data(conn, team))
        print('\t', insert_pitching_team_data(conn, team))
    conn.close()
