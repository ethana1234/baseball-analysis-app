import sqlite3
import os

def db_setup():
    # Connect to db
    # Setup db connection, conn variable is None if connection unsuccessful
    conn = None
    try:
        # Note that if db file doesn't already exist, one will be made
        # Also be weary of the check_same_thread condition, could cause problems if multiple threads try to access db
        directory = os.path.dirname(os.path.abspath(__file__))
        conn = sqlite3.connect(os.path.join(directory, '..', 'baseball.db'), check_same_thread=False)
    except Exception as e:
        # Don't continue if there's an Exception here
        db_error_cleanup(conn, e)
    return conn

def db_error_cleanup(conn, e):
    # Proper cleanup of db after catching an Exception
    conn.rollback()
    conn.close()
    raise e
