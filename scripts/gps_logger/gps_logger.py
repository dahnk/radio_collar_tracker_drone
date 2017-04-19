# -* python *-
# Usage: api start ./gps_logger.py [-d <destination>] [-p <prefix>]
#        [-r <runNum>] [-s <suffix>]
#
# Defaults to   destination:    /media/RAW_DATA/rct/
#               prefix:         GPS_
#               suffix:
#               runNum:         1
import time
import argparse
import signal
import sys
from time import sleep
import serial
sys.path.insert(0, './lib')
import ublox

def handler(signum, frame):
    global runstate
    runstate = False
    return


signal.signal(signal.SIGINT, handler)

global runstate
print("GPS_LOGGER: Started")
runstate = True

parser = argparse.ArgumentParser(description = "GPS Logging using MAVLink")
parser.add_argument('-o', '--output_dir', help = 'Output directory', metavar = 'data_dir', dest = 'dataDir', required = True)
parser.add_argument('-p', '--prefix', help = 'Output File Prefix, default "GPS_"', metavar = 'prefix', dest = 'prefix', default = 'GPS_')
parser.add_argument('-s', '--suffix', help = 'Output File Suffix, default ""', metavar = 'suffix', dest = 'suffix', default = '')
parser.add_argument('-r', '--run', help = 'Run Number', metavar = 'run_num', dest = 'runNum', required = True, type = int)
parser.add_argument('-i', '--port', help = 'NMEA port', metavar = 'port', dest = 'port', required = True)
parser.add_argument('-b', '--baud_rate', help = 'baud rate', metavar = 'baud', dest = 'baud', required = False, default = 57600, type = int)

args = parser.parse_args()
dataDir = args.dataDir
gpsPrefix = args.prefix
gpsSuffix = args.suffix
runNum = args.runNum
port = args.port
baud = args.baud

logfile = open("%s/%s%06d" % (dataDir, gpsPrefix, runNum), "w")
# stream = open("/home/ntlhui/Downloads/nmea.log");
stream = serial.Serial(port, baud, timeout = 5)
print("GPS_LOGGER: Running")


ref_time = time.time()
gps_time = 0
offset = gps_time - ref_time

while runstate:
    try:
        line = stream.readline()
    except serial.serialutil.SerialException, e:
        break

    if line is not None:
        msg = pynmea2.parse(line);
        if msg.sentence_type == 'GGA':
            logfile.write("%.3f, %d, %d, %.3f, %d, %d, %d, %d, %d, %d\n" % (time.time(),
                msg.latitude, msg.longitude, time.time() + offset, msg.altitude, -1, -1, -1, -1, 999))
                # msg.latitude, msg.longitude, time.time() + offset, msg.altitude, msg.relative_alt, msg.vx, msg.vy, msg.vz, msg.hdg))
        if msg.sentence_type == 'ZDA':
            ref_time = time.time()
            gps_time = time.mktime(time.strptime(msg.datetime.ctime()))
            offset = gps_time - ref_time
print("GPS_LOGGER: Ending thread")
logfile.close()

