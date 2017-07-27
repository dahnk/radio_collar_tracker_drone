#!/usr/bin/env python
import subprocess
import time
from enum import Enum
import threading
import os
import signal
import serial
import pynmea2

class SDR_INIT_STATES(Enum):
	find_devices = 0
	wait_recycle = 1
	usrp_probe = 2

devnull = open(os.devnull, 'w')
thread_op = True

def init_SDR():
	global thread_op
	init_sdr_state = SDR_INIT_STATES.find_devices
	while thread_op:
		if init_sdr_state == SDR_INIT_STATES.find_devices:
			uhd_find_dev_retval = subprocess.call(['/usr/local/bin/uhd_find_devices', '--args=\"type=b200\"'], stdout=devnull, stderr=devnull)
			if uhd_find_dev_retval == 0:
				init_sdr_state = SDR_INIT_STATES.usrp_probe
			else:
				init_sdr_state = SDR_INIT_STATES.wait_recycle
		elif init_sdr_state == SDR_INIT_STATES.wait_recycle:
			time.sleep(1)
			init_sdr_state = SDR_INIT_STATES.find_devices
		elif init_sdr_state == SDR_INIT_STATES.usrp_probe:
			uhd_usrp_probe_retval = subprocess.call(['/usr/local/bin/uhd_usrp_probe', '--args=\"type=b200\"', '--init-only'], stdout=devnull, stderr=devnull)
			if uhd_usrp_probe_retval == 0:
				return 0
			else:
				return 1
	return 1

class OUTPUT_DIR_STATES(Enum):
	get_output_dir = 0
	check_output_dir = 1
	check_space = 2
	wait_recycle = 3

def init_output_dir():
	global thread_op
	init_output_dir_state = OUTPUT_DIR_STATES.get_output_dir
	while thread_op:
		if init_output_dir_state == OUTPUT_DIR_STATES.get_output_dir:
			output_dir = os.environ['output_dir']
			init_output_dir_state = OUTPUT_DIR_STATES.check_output_dir
		elif init_output_dir_state == OUTPUT_DIR_STATES.check_output_dir:
			if os.path.isdir(output_dir):
				init_output_dir_state = OUTPUT_DIR_STATES.check_space
			else:
				init_output_dir_state = OUTPUT_DIR_STATES.wait_recycle
		elif init_output_dir_state == OUTPUT_DIR_STATES.check_space:
			df = subprocess.Popen(['df', output_dir], stdout=subprocess.PIPE)
			output = df.communicate()[0]
			device, size, used, available, percent, mountpoint = output.split('\n')[1].split()
			if available > 20 * 60 * 2000000 * 4:
				# enough space
				return 0
			else:
				init_output_dir_state = OUTPUT_DIR_STATES.wait_recycle
		elif init_output_dir_state == OUTPUT_DIR_STATES.wait_recycle:
			time.sleep(1)
			init_output_dir_state == OUTPUT_DIR_STATES.check_output_dir
	return 1

class GPS_STATES(Enum):
	get_tty = 0
	get_msg = 1
	wait_recycle = 2

def accept_gps(msg):
	if msg.gps_qual == 0:
		return False
	if msg.gps_qual == 7:
		return False
	if msg.gps_qual == 8:
		return False
	if msg.num_sats < 6:
		return False
	return True

def init_gps():
	global thread_op
	init_gps_state = GPS_STATES.get_tty
	while thread_op:
		if init_gps_state == GPS_STATES.get_tty:
			tty_device = os.environ['gps_port']
			tty_baud = os.environ['gps_baud']
			try:
				tty_stream = serial.Serial(tty_device, tty_baud, timeout = 5)
			except serial.SerialException, e:
				return 1
			init_gps_state = GPS_STATES.get_msg
		elif init_gps_state == GPS_STATES.get_msg:
			try:
				line = tty_stream.readline()
			except serial.serialutil.SerialException, e:
				init_gps_state = GPS_STATES.get_msg
				continue
			if line is not None:
				msg = None
				try:
					msg = pynmea2.parse(line)
				except pynmea2.ParseError, e:
					init_gps_state = GPS_STATES.get_msg
					continue
				if msg.sentence_type == 'GGA':
					if accept_gps(msg):
						# good GPS
						return 0
					else:
						init_gps_state = GPS_STATES.wait_recycle
				else:
					init_gps_state = GPS_STATES.get_msg
			else:
				init_gps_state = GPS_STATES.get_msg
		elif init_gps_state == GPS_STATES.wait_recycle:
			time.sleep(1)
			init_gps_state = GPS_STATES.get_msg

def sigint_handler(signal, frame):
	print("REceived sig")
	global thread_op
	thread_op = False

def main():
	signal.signal(signal.SIGINT, sigint_handler)
	signal.signal(signal.SIGTERM, sigint_handler)
	init_SDR_thread = threading.Thread(target=init_SDR)
	init_output_thread = threading.Thread(target=init_output_dir)
	init_SDR_thread.start()
	init_output_thread.start()
	# init_SDR_thread.join()
	signal.pause()

if __name__ == '__main__':
	main()