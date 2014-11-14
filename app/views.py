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
avewindow = 40
def listening():
    ser = serial.Serial('/dev/ttyACM0', 57600)
    global avewindow
    global otpReady
#ser.write(binascii.a2b_hex('69'))
    for addr in otpAddr:
        ser.write(binascii.a2b_hex("a5044b"+ addr['ahex'] +"00c3"))
    while True:
        if otpReady == False:
            print "Reading OTP"
            socketio.emit('status', "Reading OTP", namespace='/main')
            n = 0
            while  n < 10:
                rcv = ser.read(2)
                seq = map(ord,rcv)
                if seq[0] == 165 and seq[1] == 7:
                    rcvn = ser.read(7)
                    seqn = map(ord,rcvn)
                    if seqn[2] == otpAddr[n]['adec']:
                        buf = [seqn[3], seqn[4]]
                        otpAddr[n]['otp'] = conv16bit(buf)
                        otpAddr[n]['otpHex'] = hex(otpAddr[n]['otp'])
                        n += 1
            otpReady = True
            constFromOtp()
            socketio.emit('otp', json.dumps(otpAddr), namespace='/main')
        else:
            "OTP GOT"
            rcv = ser.read(16)
            seq = map(ord,rcv)
            pkt = parsePkt(seq)
            # pkt['alti'] = meterFromPa(pkt['pres'])
            presArrary.append(pkt['pres'])
            if len(presArrary) >= avewindow:
                socketio.emit('status', "Working", namespace='/main')
                while len(presArrary) >= avewindow:
                    presArrary.pop(0)
                ave = movingaverage(presArrary, 5)
                if avewindow == 1:
                    pkt['avePres'] = pkt['pres']
                else:
                    pkt['avePres'] = round(np.mean(ave), 2)
                dpres = int(pkt['avePres'])
                socketio.emit('push', json.dumps(pkt), namespace='/main')
                socketio.emit('dpres', json.dumps(dpres))
            else:
                socketio.emit('status', "Averaging Data", namespace='/main')
        # print(binascii.b2a_hex(rcv))
        # print pkt
        # time.sleep(1)

    ser.close()

# Open new thread for Listening function
listen = Thread(target=listening,name="ListenSensor")
# listen.daemon = True


@app.route('/')
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


@socketio.on('changeAve', namespace='/main')
def changeAve(data):
    global avewindow
    avewindow = int(data['avewindow'])
    print "avewindow changed to %d" %avewindow

@socketio.on('SEND')
def send(msg):
    print msg
    global clients
    clients += 1
    if listen.isAlive() == False:
        listen.start()
        print "Start listening to Sensor"
    else:
        print "Listening Thread already started"
        emit('status', {'msg': 'Connected', 'count': 0})

@socketio.on('connect', namespace='/main')
def connect():
    global clients
    global coeDict
    clients += 1
    print clients, "Clients Connected"
    # emit('connect',1)
    # Start listening Thread if not exist
    if listen.isAlive() == False:
        listen.start()
        print "Start listening to Sensor"
    else:
        print "Listening Thread already started"
        emit('otp', json.dumps(otpAddr), namespace='/main')

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
