import sys,requests,sqlite3,json,hashlib
import pandas as pd
import numpy as np
from datetime import datetime

# Pull all given teams data from given table and return as pandas DF
def get_teams(conn, team_codes, table):
    try:
        sql_table = dict(t='Team', b='BattingGame', p='PitchingGame')[table]
    except KeyError:
        return False
    # If team_codes list is empty, select all teams
    query = f'SELECT * FROM {sql_table}' + (f" WHERE team_code IN ({','.join(['?' for _ in team_codes])});" if team_codes else ';')
    df = pd.read_sql_query(query, conn, params=team_codes, coerce_float=False)
    return df.round(3)

if __name__=='__main__':
    conn = sqlite3.connect('D:/mydata/baseball.db')
    result = get_teams(conn, ['PHI'], 't')
    print('')

