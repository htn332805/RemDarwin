import os
import yaml
import dash
from dash import html, dcc
import plotly
from flask_login import LoginManager, login_required
from ..core.database import db_manager
from ..ingestion.models import User

# Load configuration from ../config/settings.yaml
config_path = os.path.join(os.path.dirname(__file__), '../config/settings.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Configuration file not found at {config_path}")
    config = {}
except yaml.YAMLError as e:
    print(f"Error parsing YAML configuration: {e}")
    config = {}
except Exception as e:
    print(f"Unexpected error loading configuration: {e}")
    config = {}

# Initialize Flask-Login
server = dash.Flask(__name__)
server.config['SECRET_KEY'] = config.get('auth', {}).get('secret_key', 'default-secret-key')
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    with db_manager.session() as session:
        return session.query(User).get(int(user_id))

# Initialize the Dash app with external stylesheets
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css'  # Standard Dash stylesheet
]
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

# Set up routing structure using base_layout from layouts.py
from .layouts import base_layout
app.layout = base_layout()

# Import callbacks to register them
from . import callbacks

# Define run_server method
def run_server():
    app.run(debug=True)

if __name__ == '__main__':
    run_server()