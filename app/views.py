# encoding=utf-8
from flask import render_template, session, jsonify
from flask import copy_current_request_context
from app import app
from flask.ext.socketio import send, emit
from app import socketio
from threading import Thread, current_thread

# import binascii
import datetime
import time

import json

from converter import *

clients = 0

def listening():
    ser = serial.Serial('/dev/ttyACM0', 57600)

#ser.write(binascii.a2b_hex('69'))
    while True:
        rcv = ser.read(16)
        seq = map(ord,rcv)
        pkt = parsePkt(seq)
        pkt['alti'] = meterFromPa(pkt['pres'])

        avewindow = 40
        presArrary.append(pkt['pres'])
        if len(presArrary) > avewindow:
            presArrary.pop(0)
            ave = movingaverage(presArrary, 5)
            pkt['avePres'] = np.mean(ave)
            dpres = int(pkt['avePres'])
            socketio.emit('push', json.dumps(pkt), namespace='/main')
            socketio.emit('time', pkt['time'], namespace='/main')
            socketio.emit('dpres', json.dumps(dpres))

        # print(binascii.b2a_hex(rcv))
        # print pkt
        # time.sleep(1)

    ser.close()

# Open new thread for Listening function
listen = Thread(target=listening,name="ListenSensor")
# listen.daemon = True


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
        title = 'APS Demo')


@socketio.on('my event')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
        {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
        {'data': message['data'], 'count': session['receive_count']},
        broadcast=True)

@socketio.on('SEND')
def send(msg):
    print msg
    if listen.isAlive() == False:
        listen.start()
        print "Start listening to Sensor"
    else:
        print "Listening Thread already started"
        emit('status', {'msg': 'Connected', 'count': 0})

@socketio.on('connect', namespace='/main')
def connect():
    global clients
    clients += 1
    print clients, "Clients Connected"
    # emit('connect',1)
    # Start listening Thread if not exist
    if listen.isAlive() == False:
        listen.start()
        print "Start listening to Sensor"
    else:
        print "Listening Thread already started"
        emit('status', {'msg': 'Connected', 'count': 0})

@socketio.on('connect')
def connect():
    global clients
    clients += 1
    print clients, "Clients Connected"
    # emit('connect',1)
    # Start listening Thread if not exist
    if listen.isAlive() == False:
        listen.start()
        print "Start listening to Sensor"
    else:
        print "Listening Thread already started"
        emit('status', {'msg': 'Connected', 'count': 0})

@socketio.on('disconnect', namespace='/main')
def disconnect():
    global clients
    clients -= 1
    if clients == 0:
        print 'No clients now'
    else:
        print 'Client disconnected, remain', clients

@socketio.on('disconnect')
def disconnect():
    global clients
    clients -= 1
    if clients == 0:
        print 'No clients now'
    else:
        print 'Client disconnected, remain', clients
