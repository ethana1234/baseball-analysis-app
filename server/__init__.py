from flask import Flask
from flask_cors import CORS
from server.baseball_viz import data_parse

def init_app():
    # Construct core Flask application

    # Setup connection to database and make sure tables exist
    with data_parse.db_setup() as conn:
        data_parse.create_baseball_tables(conn)

        # App instantiation
        app = Flask(__name__, instance_relative_config=False)
        app.config['DBCONN'] = conn
        CORS(app, resources={r'/*': {'origins': '*'}})
        app.config.from_object(__name__)
        with app.app_context():

            # Import Dash application
            from .baseball_viz import init_dashboard
            app = init_dashboard(app)
            
            return app
