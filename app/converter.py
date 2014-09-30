# encoding=shift_jis
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

# opt = [15740672, 33.82813745536668, 1.0595583971678823e-05, 1.0570719888912625, -9.367075716422009e-06, 1.8715130466628007e-10, 15740672, 44.30369945371868]
# -1040384
# 33.8281374553667
# -1.55337412640767E-05
# 1.05353412945952
# -8.7228131962035E-06
# 5.59473006378368E-11
# 3120224
# 40.4235810419019
CP = -1040384
BP = 33.8281374553667
AP = -1.55337412640767E-05

CT = 1.05353412945952
BT = -8.7228131962035E-06
AT = 5.59473006378368E-11

CA = 3120224
BA = 40.4235810419019

PRES_HP0 = 1013.25    # hPa in 0m of sea-surface
PRES_TNOM = 273.15    # degC to Kelvin
PRES_HDEN = 0.0065   # denominator of Height
PRES_PDEN = 5.257;     # denominator of Pressure

Tnow = 25.0
Hnow = 0.0

presArrary = []

def conv24bit(buf):
    s = (buf[0] << 16) + (buf[1] << 8) + buf[2]
    # if (s & 0x00800000) != 0:
    #     s = -(0x01000000 - s)
    return s

def conv16bit(buf):
    s = (buf[0] << 8) + buf[1];
    # if signed:
    return s

# def movingaverage(values,window):
#     weigths = np.repeat(1.0, window)/window
#     smas = np.convolve(values, weigths, 'valid')
#     return smas
def movingaverage(x, window):
    y = np.empty(len(x)-window+1)
    for i in range(len(y)):
        y[i] = np.sum(x[i:i+window])/window
    return y

def convPa(pkt):
    Dt = pkt['dptat']
    Dp = pkt['dpres']

    wk = BP * BP - (4 * AP * (CP - Dp))
    Pl = ( -1.0 * BP + math.sqrt(math.fabs(wk))) / (2 * AP)
    # Pl = AP + ((Dp + CP) ** -2) * BP

    Tr = (Dt -CA) / BA

    # Po =(1 + CT + BT * Tr + AT * (Tr ** 2)) * Pl
    # Po = Pl * (AT * Tr * Tr + BT * Tr + CT )
    Po = Pl / (AT * Tr * Tr + BT * Tr + CT)


    return Pl, Tr/256, Po

def meterFromPa(pa):
    hpa = pa/100
    ret = math.pow(PRES_HP0 / hpa, 1 / PRES_PDEN) - 1
    ret = ret * (Tnow + PRES_TNOM)
    ret = ret / PRES_HDEN + Hnow
    return ret

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
    # pkt = {}]
    now = datetime.datetime.now()
    # .strftime("%A, %d. %B %Y %I:%M%p")
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
    else:
        i = 0
        while i < len(pkt) and len(seq) > 0:
            d += seq[0]
            i += 1
            seq.pop(0)
        print d
        return None

    if len(seq) >= 1:
        pkt['chksum'] = seq[0]
        seq.pop(0)

    if len(seq) >= 1:
        if seq[0] == int(CHR_EDELIM):
            seq.pop(0)

    return pkt

