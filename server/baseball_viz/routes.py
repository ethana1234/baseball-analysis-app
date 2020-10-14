from flask import Flask, jsonify, abort, request, send_from_directory, Response, render_template
from flask import current_app as app
from io import StringIO
import pandas as pd
import numpy as np
import os, sqlite3
from . import data_parse, data_retrieve

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

# Retrieve db connection from current app
conn = app.config['DBCONN']

@app.route('/')
def home():
    return render_template(
        'index.html',
        title='Baseball analysis app',
        description='View and graph 2020 MLB game data.',
        template='home-template',
        body="This is a homepage served with Flask."
    )


# Test route
@app.route('/hello', methods=['GET'])
def helloWorld():
    return 'Hello World! I am the backend.'

# Icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'favicon.ico')

# Add a team's data (Batting, Pitching, and Team)
@app.route('/addTeam/<team_code>', methods=['POST'])
def add_a_team(team_code):
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
    conn.commit()
    return jsonify(response_object)

# Use route parameter (only single team)
@app.route('/teams/<team_code>/<table>', methods=['GET'])
def get_single_team(team_code, table='t'):
    response_object = {'status': 'success'}
    if team_code not in all_team_codes:
        abort(406, description='Invalid team code')
    response_object['data'] = data_retrieve.get_teams(conn, [team_code], table).to_dict('records')
    if response_object['data'] is False:
        abort(406, description='Invalid table')
    # Return list of dictonaries, each dict is a row
    return jsonify(response_object)

# Use request body (can do multiple teams)
# Request body can choose csv format as well with format attribute, default is JSON
# Use query string (/teams?team_code={team_code}&table={t, b, or p}) for a single team
# No team_codes attribute returns all teams, no table attribute returns Team table
@app.route('/teams', methods=['GET'])
def get_teams():
    response_object = {'status': 'success'}
    get_data = request.get_json()
    query_team_code = request.args.get('team_code')
    get_data = dict(team_codes=[query_team_code] if query_team_code is not None else [], table=request.args.get('table', 't')) if get_data is None else get_data
    team_codes = get_data.get('team_codes', [])
    if not set(team_codes).issubset(all_team_codes):
        abort(406, description='Invalid team code')
    response_object['data'] = data_retrieve.get_teams(conn, team_codes, get_data.get('table', 't'))
    if response_object['data'] is False:
        abort(406, description='Invalid table')
    if get_data.get('format', 'json') == 'csv':
        output = StringIO()
        response_object['data'].to_csv(output, index=False)
        return Response(output.getvalue(), mimetype="text/csv")
    response_object['data'] = response_object['data'].to_dict('records')
    # Return list of dictonaries, each dict is a row
    return jsonify(response_object)
