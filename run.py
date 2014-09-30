#!flask/bin/python
from app import app
from app import socketio

app.debug=True
app.threaded=True
app.config['SECRET_KEY'] = 'secret!'

socketio.run(app, host='0.0.0.0')
