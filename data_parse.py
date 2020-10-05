import sys,requests,sqlite3,json,hashlib
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

sql_max_int = 2147483647

def db_setup():
    # Connect to db
    # Setup db connection, conn variable is None if connection unsuccessful
    conn = None
    try:
        # Note that if db file doesn't already exist, one will be made
        conn = sqlite3.connect('D:/mydata/baseball.db')
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
    #   Fix Date column for double headers
    data['Date'] = data['Date'].str.slice(stop=5)
    #   Generate unique game id for each game and make it the index
    game_ids = [data['Date'].iloc[i] + ((data['Opp'].iloc[i] + team_code) if data['HomeAway'].iloc[i] == 'H' else (team_code + data['Opp'].iloc[i])) + data['Opp. Starter (GmeSc)'].iloc[i] for i in range(len(data.index))]
    game_ids = [int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % sql_max_int for s in game_ids]
    data['game_id'] = game_ids
    data.set_index('game_id', inplace=True)
    # Add team id based on 3 letter team code
    team_ids = [sum([ord(char) for char in team_code]) for i in range(len(data.index))]
    data['team_id'] = team_ids
    #   Drop unneccessary columns and reorder the remains
    data.drop(columns=['Rslt', 'Rk', 'Gtm', 'Opp. Starter (GmeSc)'], inplace=True)
    data = data[['team_id', 'Date', 'HomeAway', 'Opp', 'Result', 'RunsAgainst', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'IBB', 'SO', 'HBP', 'SH', 'SF',
                'ROE', 'GDP', 'SB', 'CS', 'LOB', 'PlayersUsed', 'BA', 'OBP', 'SLG', 'OPS', 'OppStarterThr']]
    #   Convert numeric columns to numeric types
    data.loc[:, 'RunsAgainst':'PlayersUsed'] = data.loc[:, 'RunsAgainst':'PlayersUsed'].apply(pd.to_numeric)
    data.loc[:, 'BA':'OPS'] = data.loc[:, 'BA':'OPS'].apply(pd.to_numeric)

    return data


def insert_batting_team_data(conn, team_code):
    # Retrieve JSON pitch data from Baseball Reference
    url = f'https://www.baseball-reference.com/teams/tgl.cgi?team={team_code}&t=b&year=2020'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err

    # Retrieve Batting Table from XML page and put into a DataFrame
    soup = BeautifulSoup(r.content, "lxml")
    table = soup.find('table')
    data = pd.read_html(str(table))[0]

    clean_data = clean_batting_data(data, team_code)

    try:
        clean_data.to_sql('BattingGame', conn, if_exists='append')
        conn.commit()
    except sqlite3.IntegrityError:
        print('Team already added')
    except Exception as e:
        db_error_cleanup(conn, e)

def insert_team_data(conn, team_code):
    pass


conn = db_setup()
create_baseball_tables(conn)
insert_batting_team_data(conn, 'PHI')
insert_team_data(conn, 'PHI')