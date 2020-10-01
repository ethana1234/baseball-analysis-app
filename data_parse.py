import sys,requests,sqlite3,json
from requests.exceptions import HTTPError

def db_setup():
    # Connect to db
    # Setup db connection, conn variable is None if connection unsuccessful
    conn = None
    try:
        # Note that if db file doesn't already exist, one will be made
        conn = sqlite3.connect('baseball.db')
    except Exception as e:
        # Don't continue if there's an Exception here
        sys.stdout = sys.stderr
        db_error_cleanup(conn, None)
        raise e
    return conn

def create_tables(conn):
    # Setup the gamefeed table on the db if not done already
    gamefeed_pitch = '''
CREATE TABLE IF NOT EXISTS gamefeed_pitch (
    play_id text PRIMARY KEY,
    game_pk integer NOT NULL,
    ab_number integer NOT NULL,
    pitch_number integer NOT NULL,
    inning integer NOT NULL,
    team_fielding_id integer NOT NULL,
    team_batting_id integer NOT NULL,
    pitcher integer NOT NULL,
    p_throws text NOT NULL,
    player_total_pitches integer NOT NULL,
    player_total_pitches_pitch_types integer NOT NULL,
    batter integer NOT NULL,
    stand text NOT NULL,
    balls integer NOT NULL,
    strikes integer NOT NULL,
    call text NOT NULL,
    description text NOT NULL,
    is_bip_out text NOT NULL,
    start_speed real NOT NULL,
    end_speed real NOT NULL,
    pitch_type text NOT NULL,
    hit_angle integer,
    hit_distance integer,
    hit_speed real,
    xba real,
    FOREIGN KEY (team_fielding_id) REFERENCES team (id),
    FOREIGN KEY (team_batting_id) REFERENCES team (id)
)'''
    db_cursor = None
    try:
        db_cursor = conn.cursor()
        db_cursor.execute(gamefeed_pitch)
        db_cursor.close()
    except Exception as e:
        print('The following error occurred while creating the gamefeed_pitch table:')
        db_error_cleanup(conn, db_cursor)

def db_error_cleanup(conn):
    # Proper cleanup of db after catching an Exception
    if conn.cursor():
        conn.cursor().close()
    if conn:
        conn.close()
    sys.exit()

def fetch_gamefeed(game_id):
    # Retrieve JSON pitch data from Baseball Savant API
    url = f'https://baseballsavant.mlb.com/gf?game_pk={game_id}'
    try:
        r = requests.get(url)
        # If the response was successful, no exception will be raised
        r.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        exit(1)
    data = r.json()
    print(type(data))
    return data


fetch_gamefeed(531432)