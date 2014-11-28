# encoding=utf-8
import serial
import binascii
import datetime
import time
import copy
import math
import numpy as np


CHR_DELIM = 0xA5
CHR_EDELIM = 0xC3
CHR_ACK = 'A'
CHR_SETUP = 'S'
CHR_RECEVIE ='R'


PRES_HP0 = 1013.25    # hPa in 0m of sea-surface
PRES_TNOM = 273.15    # degC to Kelvin
PRES_HDEN = 0.0065   # denominator of Height
PRES_PDEN = 5.257;     # denominator of Pressure

Tnow = 25.0
Hnow = 0.0

otpReady = False
otpAddr = [
    {"name": "CEX", "ahex": "b2", "adec": 178, "k": None, "a": None, "s": None},
    {"name": "PTAT3", "ahex": "a0", "adec": 160, "k": None, "a": None, "s": None},
    {"name": "PTAT2", "ahex": "b0", "adec": 176, "k": "ba", "a": 4.18E+01, "s": 1.94},
    {"name": "PTAT1", "ahex": "b2", "adec":178, "k": "ca", "a": "offset", "s": "offset"},
    {"name": "TEMP3", "ahex": "b4", "adec":180, "k": "ct", "a": 1.0563, "s": 7.56E-03},
    {"name": "TEMP2", "ahex": "b6", "adec":182, "k": "bt", "a": -9.41E-06, "s": 1.45E-06},
    {"name": "TEMP1", "ahex": "b8", "adec":184, "k": "at", "a": 9.64E-11, "s": 6.56E-11},
    {"name": "PR3", "ahex": "ba", "adec":186, "k": "cp", "a": "offset", "s": "offset"},
    {"name": "PR2", "ahex": "bc", "adec":188, "k": "bp", "a": 3.37E+01, "s": 6.42},
    {"name": "PR1", "ahex": "be", "adec":190, "k": "ap", "a": -1.53E-05, "s": 1.38E-05},
]
coeDict = {}

presArrary = []

def conv24bit(buf):
    s = (buf[0] << 16) + (buf[1] << 8) + buf[2]
    return s

def conv16bit(buf):
    s = (buf[0] << 8) + buf[1];
    return s

def conv16Sign(s):
    if s >= 0:
        if s & 0x8000 != 0:
            s = s - 65536
    return s

def conv24Sign(s):
    if s >= 0:
        if s & 8388608 != 0:
            s = s - 16777216
    return s

def constFromOtp():
    global coeDict
    for elem in otpAddr:
        if elem['k'] != None and elem['a'] != "offset":
            result = elem['a'] + conv16Sign(elem['otp']) * elem['s']  / 32767.0
            coeDict[elem['k']] =  result
        elif elem['a'] == "offset":
            PTAT1 = filter(lambda d: d['name'] == "PTAT1",  otpAddr)[0]['otp']
            PTAT3 = filter(lambda d: d['name'] == "PTAT3",  otpAddr)[0]['otp']
            if elem['k'] == "ca":
                ret = elem['otp'] & 0xff
                coeDict[elem['k']] = (ret << 16) | PTAT3
            if elem['k'] == "cp":
                ret = (PTAT1 & 0xff00) >> 8
                coeDict[elem['k']] = conv24Sign((ret << 16)) | elem['otp']
    print coeDict

def movingaverage(x, window):
    if len(x) > window+1:
        y = np.empty(len(x)-window+1)
        for i in range(len(y)):
            y[i] = np.sum(x[i:i+window])/window
        return y
    else:
        return x

def convPa(pkt):
    Dt = pkt['dptat']
    Dp = pkt['dpres']

    wk = coeDict['bp'] * coeDict['bp'] - (4 * coeDict['ap'] * (coeDict['cp'] - Dp))
    Pl = ( -1.0 * coeDict['bp'] + math.sqrt(math.fabs(wk))) / (2 * coeDict['ap'])

    Tr = (Dt -coeDict['ca']) / coeDict['ba']

    Po = Pl / (coeDict['at'] * Tr * Tr + coeDict['bt'] * Tr + coeDict['ct'])


    return round(Pl, 2), round(Tr/256, 2), round(Po, 2)

def paToAlti(pa, t, P0):
    hpa = pa/100
    z = (t + 273.15) * (1 - (hpa/P0) ** (1/5.257))/0.0065
    return round(z, 2)

def skipToDelim(seq):
    while(len(seq) > 0):
        if seq[0] == CHR_DELIM:
            return True
        seq.pop(0)
        return False

def checkPenalty(seq):
    mPenalty += 1
    if mPenalty >= mPenaltyMax:
        seq = []
    return None

def parseRecPkt(pkt, buf):
    now = datetime.datetime.now()
    pkt['time'] = now.strftime("%A, %d. %B %Y %I:%M:%S%p")
    pkt['dpres'] = getPres(buf)
    pkt['dptat'] = getTemp(buf)
    if len(buf) >= 1:
        pkt['sensor'] = buf[0]
        buf.pop(0)
    if len(buf) >= 1:
        pkt['data'] =buf[1]
        buf.pop(0)
    pkt['pl'],pkt['temp'], pkt['pres'] = convPa(pkt)
    return pkt
    # print pkt

def getPres(buf):
    ret = 0
    if len(buf) < 0:
        return ret
    if len(buf) >= 3:
        ret = conv24bit(buf)
    for i in xrange(0,3):
        buf.pop(0)
    return ret

def getTemp(buf):
    ret = 0
    if len(buf) < 2:
        return ret
    if len(buf) >= 2:
        ret = conv16bit(buf)
        ret <<= 8
    for i in xrange(0,2):
        buf.pop(0)
    return ret

def parsePkt(seq):
    ret = skipToDelim(seq)
    if not ret:
        return None

    if len(seq) < 3:
        checkPenalty(seq)
        return None

    pkt = {}
    pkt['delim'] = seq[0]
    n = seq[1]
    pkt['datalen'] = seq[1]
    pkt['type'] = chr(seq[2])

    if len(seq) < (n + 2):
        checkPenalty(seq)
        return None

    mPenalty = 0
    seq.pop(0)
    seq.pop(0)
    seq.pop(0)


    if pkt['type'] == CHR_RECEVIE:
        parseRecPkt(pkt, seq)
    elif pkt['type'] == CHR_ACK:
        # parseAckPkt
        pass
    # else:
    #     i = 0
    #     d = 0
    #     while i < len(pkt) and len(seq) > 0:
    #         d += seq[0]
    #         i += 1
    #         seq.pop(0)
    #     print d
    #     return None

    if len(seq) >= 1:
        pkt['chksum'] = seq[0]
        seq.pop(0)

    if len(seq) >= 1:
        if seq[0] == int(CHR_EDELIM):
            seq.pop(0)

    return pkt

