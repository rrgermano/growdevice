import os
import RPi.GPIO as gpio
import time
from multiprocessing import Process
from indicator import NetStatus


class WPS(Process):
	def __init__(self):
		Process.__init__(self)
		self.button = 11
		gpio.setmode(gpio.BCM)
		gpio.setup(self.button, gpio.IN, pull_up_down=gpio.PUD_UP)
		self.net = NetStatus()
		self.net.start()
		self.flag_stop = False

	def run(self):
		btn_time = 0
		while True:
			if gpio.input(self.button) == gpio.LOW:
				if btn_time == 0:
					btn_time = time.time()
				if time.time() - btn_time > 2:
					os.system("wpa_cli -i wlan0 wps_pbc")
					state = self.net.status()
					connect_time = time.time()
					while state != "COMPLETED":
						state = self.net.status()
						if time.time() - connect_time>60:
							break
					btn_time = 0
			else:
				btn_time = 0
			if self.flag_stop:
				break

	def stop(self):
		self.flag_stop = True
		self.net.stop()
