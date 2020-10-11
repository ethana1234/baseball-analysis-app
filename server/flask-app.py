from flask import Flask, jsonify, abort, request, send_from_directory
from flask_cors import CORS
import data_parse, os, sqlite3

# App instantiation
app = Flask(__name__)
app.config.from_object(__name__)
debug = True
CORS(app, resources={r'/*': {'origins': '*'}})

# Global variables
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

# Setup connection to database and make sure tables exist
conn = data_parse.db_setup()
data_parse.create_baseball_tables(conn)

# Test route
@app.route('/hello', methods=['GET'])
def helloWorld():
    return 'Hello World! I am the backend.'

# Icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'images'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# POST: Add a team's data (Batting, Pitching, and Team)
# GET: Retrieve a team's data from Team table
@app.route('/team/<team_code>', methods=['GET', 'POST'])
def single_team(team_code):
    response_object = {'status': 'success'}
    if team_code not in all_team_codes:
        abort(406, description='Invalid team code')
    if request.method == 'POST':
        team_result = data_parse.insert_team_data(conn, team_code)
        if not team_result:
            abort(500, description=f'Issue adding {team_code}')
        elif team_result == 'Team exists':
            response_object['message'] = f'{team_code} already in the database.'
            return jsonify(response_object)
        batting_result = data_parse.insert_batting_team_data(conn, team_code)
        pitching_result = data_parse.insert_pitching_team_data(conn, team_code)
        if batting_result and pitching_result:
            response_object['message'] = f'{team_code} added!'
        else:
            conn.rollback()
            abort(500, description=f'Issue adding {team_code} data')
    #elif request.method == 'GET':
    conn.commit()
    return jsonify(response_object)


if __name__=='__main__':
    app.run(debug=debug)
