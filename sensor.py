import AWSIoT

import adafruit_dht
import time
import average
from threading import Thread
import math
import board


class Temperature(Thread):
    def __init__(self, break_time, client_id="temperature"):
        Thread.__init__(self)
        self.break_time = break_time
        self.client_id = client_id
        self.iot = AWSIoT.IoT(self.client_id)
        self.conjugate_sensor = adafruit_dht.DHT22(board.D2)
        #self.sensor_pin = 2
        self.temperature = average.average(size=30, error=5)
        self.humidity = average.average(error=20)
        self.last_meas = 0
        self.flag_stop = False
        self.leaf_temp = 2
        self.vpd = 100
        #for i in range(2):
        #    Adafruit_DHT.read(self.conjugate_sensor, self.sensor_pin)

    def run(self):
        contract_temp = {}
        humid = None
        temp = None
        while True:
            if time.time() - self.last_meas > self.break_time:
                self.last_meas = time.time()
                try:
                    humid = self.conjugate_sensor.humidity
                    temp = self.conjugate_sensor.temperature
                except:
                    pass
                if temp is not None:
                    new_temp = self.temperature.average(temp)
                if humid is not None:
                    new_humid = self.humidity.average(humid)
                if len(self.temperature.itens) > 2:
                    if self.temperature.itens[-1] != self.temperature.itens[-2]:
                        contract_temp['temperature'] = round(new_temp, 2)
                if len(self.humidity.itens) > 2:
                    if self.humidity.itens[-1] != self.humidity.itens[-2]:
                        contract_temp['humidity'] = round(new_humid, 2)
                if self.vpd != self.vpd_calc():
                    self.vpd = self.vpd_calc()
                    contract_temp['vpd'] = round(self.vpd, 2)
                if len(contract_temp) != 0:
                    self.iot.post(contract_temp, 'sensor_data')
                contract_temp = {}
                humid = None
                temp = None
                if self.flag_stop:
                    break

    def get_data(self):
        return round(self.temperature.average(),2), round(self.humidity.average(), 2 ), round(self.vpd, 2)

    def vpd_calc(self):
        self.asvp = 610.78 * math.e ** ((self.temperature.average() / (self.temperature.average() + 238.3)) * 17.2964)
        self.lsvp = 610.78 * math.e ** (((self.temperature.average() - self.leaf_temp) / (
                    self.temperature.average() - self.leaf_temp + 238.3)) * 17.2964)
        return (self.lsvp - (self.asvp * (self.humidity.average() / 100))) / 1000


    def stop(self):
        self.flag_stop = True
