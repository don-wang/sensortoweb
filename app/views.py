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
import glob

from converter import *

def scan():
    return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')

sensor = '/dev/ttyACM0'
clients = 0
avewindow = 40
P0 = 1013.25
def listening():
    while ('ser' in locals()) == False:
        ports = scan()
        if sensor in ports:
            ser = serial.Serial(sensor, 38400)
        else:
            print "Device " + sensor + " not found, wait for operation"
            time.sleep(30)
    global avewindow
    global P0
    global otpReady

#ser.write(binascii.a2b_hex('69'))

    while otpReady == False:
        print "Reading OTP"
        n = 0
        while  n < 10:
            ser.write(binascii.a2b_hex("a5044b"+ otpAddr[n]['ahex'] +"00c3"))
            socketio.emit('status', "Reading OTP", namespace='/main')
            socketio.emit('otp', json.dumps(otpAddr), namespace='/main')
            rcv = ser.read(2)
            seq = map(ord,rcv)
            if seq[0] == 165 and seq[1] == 7:
                rcvn = ser.read(7)
                seqn = map(ord,rcvn)

                if seqn[2] == otpAddr[n]['adec']:
                    buf = [seqn[3], seqn[4]]
                    otpAddr[n]['otp'] = conv16bit(buf)
                    otpAddr[n]['otpHex'] = hex(otpAddr[n]['otp'])
                    print otpAddr[n]['name'], otpAddr[n]['otpHex']
                    n += 1
        otpReady = True
        constFromOtp()
        socketio.emit('otp', json.dumps(otpAddr), namespace='/main')

    while True:
        "OTP GOT"
        rcv = ser.read(2)
        seq = map(ord,rcv)
        while seq[0] != 165 or seq[1] != 14:
            rcv = ser.read(2)
            seq = map(ord,rcv)
        rcv = ser.read(14)
        rcv = ser.read(16)
        seq = map(ord,rcv)
        pkt = parsePkt(seq)

        if 'pres' in pkt:
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
            pkt['alti'] = paToAlti(pkt['avePres'], pkt['temp'], P0)
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

@socketio.on('changeSeaLev', namespace='/main')
def changeSeaLev(data):
    global P0
    if 'sealevel' in data and data['sealevel']/1.0 != 0:
        P0 = data['sealevel']/1.0
    else:
        P0 = 1.0
    print "avewindow changed to %d" %P0

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
