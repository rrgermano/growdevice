import RPi.GPIO as Gpio
import time
from threading import Thread
import os
import requests


class Indicator (Thread):
    def __init__(self):
        Thread.__init__(self)
        self.__red = 23
        self.__green = 10
        self.__blue = 9
        self.__central = 22
        Gpio.setwarnings(False)
        Gpio.setmode(Gpio.BCM)
        Gpio.setup(self.__red, Gpio.OUT, initial=Gpio.HIGH)
        Gpio.setup(self.__green, Gpio.OUT, initial=Gpio.HIGH)
        Gpio.setup(self.__blue, Gpio.OUT, initial=Gpio.HIGH)
        Gpio.setup(self.__central, Gpio.OUT, initial=Gpio.LOW)
        self.pwm = Gpio.PWM(self.__central, 60)
        self.current_color = self.__red
        self.interval = 2/100
        self.flag_stop = False

    def run(self):
        now = 0
        i = 0
        Gpio.output(self.current_color, 0)
        self.pwm.start(i)
        while True:
            while i < 100:
                if time.time()-now > self.interval:
                    if now == 0:
                        now = time.time()
                    if self.flag_stop:
                        self.pwm.ChangeDutyCycle(0)
                        break
                    i += int((time.time() - now)/self.interval)
                    if i > 100:
                        i = 100
                    self.pwm.ChangeDutyCycle(i)
                    now = time.time()
            while i > 0:
                if time.time() - now > self.interval:
                    if now == 0:
                        now = time.time()
                    if self.flag_stop:
                        self.pwm.ChangeDutyCycle(0)
                        break
                    i -= int((time.time() - now)/self.interval)
                    if i < 0:
                        i = 0
                    self.pwm.ChangeDutyCycle(i)
                    now = time.time()
            if self.flag_stop:
                self.pwm.ChangeDutyCycle(100)
                Gpio.cleanup()
                break

    def change_light(self, color, interval):
        self.interval = interval/100

        if color == 'red' and self.current_color != self.__red:
            Gpio.output(self.current_color, 1)
            self.current_color = self.__red
            Gpio.output(self.current_color, 0)
        elif color == 'blue' and self.current_color != self.__blue:
            Gpio.output(self.current_color, 1)
            self.current_color = self.__blue
            Gpio.output(self.current_color, 0)
        elif color == 'green' and self.current_color != self.__green:
            Gpio.output(self.current_color, 1)
            self.current_color = self.__green
            Gpio.output(self.current_color, 0)

    def stop(self):
        self.flag_stop = True


class NetStatus(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.led = Indicator()
        self.flag_stop = False

    def internet(self):
        try:
            requests.get('https://www.google.com', timeout=1.5)
            return True
        except:
            return False

    def status(self):
        state = None
        keys = os.popen("wpa_cli -i wlan0 status").read().split("\n")
        for i in keys:
            if "wpa_state" in i:
                state = keys[keys.index(i)][10:]
        if state is None:
            state = "DISABLED"
        return state

    def run(self):
        while True:
            status = self.status()
            internet = self.internet()
            if status == 'COMPLETED' and not internet:
                self.led.change_light('blue', 2)
            elif status == 'COMPLETED' and internet:
                self.led.change_light('green', 3)
            elif status == 'ASSOCIATING' or self.status() == 'ASSOCIATED':
                self.led.change_light('blue', .5)
            elif status == 'SCANNING':
                self.led.change_light('red', .5)
            elif status == 'DISCONNECTED' or status == 'DISABLED':
                self.led.change_light('red', 2)
            if not self.led.is_alive():
                self.led.start()
            if self.flag_stop:
                self.led.stop()
                break

    def stop(self):
        self.flag_stop = True
