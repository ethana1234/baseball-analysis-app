import sys,requests,sqlite3,json
from requests.exceptions import HTTPError

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
    CREATE TABLE IF NOT EXISTS Batting (
        game_id integer NOT NULL,
        team_id integer NOT NULL,
        fly_outs integer,
        ground_outs integer,
        runs integer,
        singles integer,
        doubles integer,
        triples integer,
        home_runs integer,
        strike_outs integer,
        walks integer,
        intentional_walks integer,
        hits integer,
        hit_by_pitch integer,
        BA real,
        AB integer,
        OBP real,
        SLG real,
        OPS real,
        caught_stealing integer,
        bases_stolen integer,
        stolen_base_percentage real,
        ground_into_double_play integer,
        ground_into_triple_play integer,
        plate_appearances integer,
        total_bases integer,
        RBI integer,
        LOB integer,
        sac_bunts integer,
        sac_flies integer,
        catchers_interference integer,
        pickoffs integer,
        PRIMARY KEY(game_id, team_id)
    )''')
    queries.append('''
    CREATE TABLE IF NOT EXISTS Pitching (
        game_id integer NOT NULL,
        team_id integer NOT NULL,
        ground_outs integer,
        air_outs integer,
        runs integer,
        singles integer,
        doubles integer,
        triples integer,
        home_runs integer,
        strike_outs integer,
        walks integer,
        intentional_walks integer,
        hits integer,
        hit_by_pitch integer,
        AB integer,
        OBP real,
        caught_stealing integer,
        stolen_bases integer,
        stolen_base_percentage real,
        ERA real,
        IP real,
        save_oppurtunities integer,
        earned_runs integer,
        WHIP real,
        batter_faced integer,
        outs integer,
        complete_games integer,
        shutouts integer,
        balks integer,
        wild_pitches integer,
        pickoffs integer,
        RBI integer,
        inherited_runners integer,
        inherited_runners_scored integer,
        catchers_interference integer,
        sac_bunts integer,
        sac_flies integer,
        PRIMARY KEY(game_id, team_id)
    )''')
    for query in queries:
        create_table(conn, query)

def fetch_gamefeed(game_id):
    # Retrieve JSON pitch data from Baseball Savant API
    url = f'https://baseballsavant.mlb.com/gf?game_pk={game_id}'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        raise http_err
    data = r.json()
    return data

def insert_batting(conn, data, game_id):
    batting_query = []
    for team in ['home', 'away']:
        batting_data = data[team]['teamStats']['batting']
        singles = batting_data['hits'] - (batting_data['doubles'] + batting_data['triples'] + batting_data['homeRuns'])
        for stat in ['avg', 'obp', 'slg', 'ops', 'stolenBasePercentage']:
            batting_data[stat] = float(batting_data[stat]) if batting_data[stat] != '.---' else None
        batting_data = list(batting_data.values())[:-1]
        batting_query.append((game_id, data[team]['team']['id'], *batting_data, singles))
    # Insert into Batting table for game
    batting_box_score = '''
    INSERT INTO Batting (
        game_id,
        team_id,
        fly_outs,
        ground_outs,
        runs,
        doubles,
        triples,
        home_runs,
        strike_outs,
        walks,
        intentional_walks,
        hits,
        hit_by_pitch,
        BA,
        AB,
        OBP,
        SLG,
        OPS,
        caught_stealing,
        bases_stolen,
        stolen_base_percentage,
        ground_into_double_play,
        ground_into_triple_play,
        plate_appearances,
        total_bases,
        RBI,
        LOB,
        sac_bunts,
        sac_flies,
        catchers_interference,
        pickoffs,
        singles)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
    try:
        conn.cursor().executemany(batting_box_score, batting_query)
        conn.commit()
    except sqlite3.IntegrityError:
        print('Game already added')
    except Exception as e:
        db_error_cleanup(conn, e)

def insert_pitching(conn, data, game_id):
    pitching_query = []
    for team in ['home', 'away']:
        pitching_data = data[team]['teamStats']['pitching']
        singles = pitching_data['hits'] - (pitching_data['doubles'] + pitching_data['triples'] + pitching_data['homeRuns'])
        for stat in ['obp', 'era', 'inningsPitched', 'stolenBasePercentage', 'whip']:
            pitching_data[stat] = float(pitching_data[stat]) if pitching_data[stat] != '.---' else None
        for stat in ['hitBatsmen', 'groundOutsToAirouts', 'runsScoredPer9', 'homeRunsPer9']:
            pitching_data.pop(stat)
        pitching_data = list(pitching_data.values())
        pitching_query.append((game_id, data[team]['team']['id'], *pitching_data, singles))
    # Insert into Pitching table for game
    pitching_box_score = '''
    INSERT INTO Pitching (
        game_id,
        team_id,
        ground_outs,
        air_outs,
        runs,
        doubles,
        triples,
        home_runs,
        strike_outs,
        walks,
        intentional_walks,
        hits,
        hit_by_pitch,
        AB,
        OBP,
        caught_stealing,
        stolen_bases,
        stolen_base_percentage,
        ERA,
        IP,
        save_oppurtunities,
        earned_runs,
        WHIP,
        batter_faced,
        outs,
        complete_games,
        shutouts,
        balks,
        wild_pitches,
        pickoffs,
        RBI,
        inherited_runners,
        inherited_runners_scored,
        catchers_interference,
        sac_bunts,
        sac_flies,
        singles)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
    try:
        conn.cursor().executemany(pitching_box_score, pitching_query)
        conn.commit()
    except sqlite3.IntegrityError:
        print('Game already added')
    except Exception as e:
        db_error_cleanup(conn, e)

db = db_setup()
create_baseball_tables(db)

game_id = 631152
data = fetch_gamefeed(game_id)
insert_batting(db, data['boxscore']['teams'], game_id)
insert_pitching(db, data['boxscore']['teams'], game_id)