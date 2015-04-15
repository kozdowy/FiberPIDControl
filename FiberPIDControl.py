#notes:
# include GUI
#   shows voltage, time, snapshot of maybe past minute,
#   and current input, with a line showing desired point
# develop better PID
# modulize better so it's easier to change
import u6
import time
import math
from visa import *
from pyvisa.visa import *
import pyvisa.vpp43 as vpp43
import matplotlib.pyplot as plt
import numpy as np
from PID import PID

current_milli_time = lambda: int(round(time.time() * 1000))

def getResult(res):
    a = res.split(',')
    return float(a[0].strip('+'))

def setPSU(vi, voltage, current):
    buf = ":volt " + str(voltage) + ";:curr " + str(current) + "\n"
    vpp43.write(vi, buf)
    buf = ":apply?\n"
    vpp43.write(vi, buf)
    result = vpp43.read(vi, 256)
    return result

def readValue(d):
    POSITIVE_CHANNEL = 2
    GAIN_INDEX = 1
    RESOLUTION_INDEX = 12
    AIN_FEEDBACK_COMMAND = u6.AIN24(POSITIVE_CHANNEL, GainIndex = GAIN_INDEX, ResolutionIndex = RESOLUTION_INDEX, Differential = 1)
    bits, = d.getFeedback(AIN_FEEDBACK_COMMAND)
    volts = d.binaryToCalibratedAnalogVoltage(GAIN_INDEX, bits)
    return volts

def initPSU():
    IPaddr = "192.168.6.6"
    defaultRm = vpp43.open_default_resource_manager()
    if defaultRm < VI_SUCCESS:
        print "status < VI_SUCCESS, quitting"
        quit()
    rsc = []
    rsc.extend([] * 256)
    rsc = "TCPIP::192.168.6.6::2268::SOCKET"
    accessMode = VI_NO_LOCK
    timeout = 0
    vi = vpp43.open(defaultRm, rsc, accessMode, timeout)
    vpp43.set_attribute(vi, VI_ATTR_TMO_VALUE, 10000)
    vpp43.set_attribute(vi, VI_ATTR_TERMCHAR_EN, VI_TRUE)
    setPSU(vi, 0, 0)
    return vi

def setSetpoint():
    setpoint = raw_input("Enter desired setpoint: ")
    setpoint = float(setpoint)
    return setpoint

def setDuration():
    duration = raw_input("Input time in minutes: ")
    duration = float(duration)
    return duration * 60

def initLabJack():
    d = u6.U6()
    d.configU6()
    d.getCalibrationData()
    return d

def writeToFile(data):
    f = open("PIDTest%s.csv" % time.strftime("%c"), 'w')
    for point in data:
        f.write(str(point[0]))
        f.write(",")
        f.write(str(point[1]))
        f.write(",")
        f.write(str(point[2]))
        f.write("\n")
    f.close()

def makePlot(data):
    table = np.array(data).T
    plt.ion()
    plt.figure(1)
    plt.plot(table[1], table[0])
    plt.figure(2)
    plt.plot(table[1], table[2])
    plt.show(block=True)

def getNewOutput(setpoint, output, reading):
    print setpoint
    print reading
    if setpoint > reading:
            print "setpoint > reading"
            returnValue = 0
    else:
            returnValue = 80
    return returnValue

vpp43.visa_library.load_library("")
d = initLabJack()
vi = initPSU()
setpoint = setSetpoint()
p = PID(800000, 0, 0)
p.setPoint(setpoint)
startTime = int(time.time())
count = 0
table = []
currentRead = []
timePassed = 0
lastTime = 0
data = []
pidread = []
volts = 0
cur = 15
current = readValue(d)
duration = setDuration()
startmilli = current_milli_time()
while timePassed < duration:
       print "Time Passed: ", timePassed
       currentRead = []
       timePassed = int(time.time() - startTime)
       vRead = readValue(d)
       currentRead.append(vRead)
       print "Current reading: ", vRead
       currentRead.append(current_milli_time() - startmilli)
       #volts = getNewOutput(setpoint, volts, vRead)
       volts = 80 - p.update(vRead)
       print "PID value: ", volts
       currentRead.append(volts)
       table.append(currentRead)
       pidread.append(volts)
       result = setPSU(vi, volts, cur)
       print "Voltage setting: ", result
result = setPSU(vi, 0, 0)
writeToFile(table)
makePlot(table)
vpp43.close(vi)
d.close();
