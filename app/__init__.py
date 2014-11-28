from flask import Flask
from flask.ext.socketio import SocketIO
from flask.ext.cors import CORS

app = Flask(__name__)
cors = CORS(app)
socketio = SocketIO(app)
from app import views