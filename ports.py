import AWSIoT
import sensor

import RPi.GPIO as Gpio
import time
from multiprocessing import Process, Pipe
import json
# from simple_pid import PID



class ShadowCallbackContainer:
    def __init__(self, device_shadow_instance):
        self.device_shadow_instance = device_shadow_instance

    def callback_delta(self, payload, *_):
        Ports.contract_receive = (json.loads(payload)['state'])
        with open("./licenses/ports.json", 'w') as f:
            f.write(json.dumps(Ports.contract_receive))
            f.close()


class Ports(Process):
    def __init__(self, break_time=15, client_id="portControl"):
        self.break_time = break_time
        self.client_id = client_id
        self.sensor = sensor.Temperature(self.break_time)
        self.sensor.start()
        self.light_port = 17
        self.light_flag = True
        self.flag_stop = False
        self.__pipe_parent,  self.__pipe_child = Pipe()
        self.iot = AWSIoT.IoT(self.client_id, pipe=self.__pipe_child).start()
        self.contract_receive = json.loads(open("./licenses/ports.json", 'r').read())
        #print(self.contract_receive)

        Gpio.setwarnings(False)
        Gpio.setmode(Gpio.BCM)
        Gpio.setup(self.light_port, Gpio.OUT)
        Process.__init__(self)
        self.light_state = json.loads(open("./licenses/light.json", 'r').read())['light_state']
        Gpio.output(self.light_port, self.light_state)
#        gpio.setup(13, gpio.OUT)

    def port_handler(self, key):

        if self.contract_receive[key]['mode'] == 'temperature':
            return self.sensor.get_data()[0]
        elif self.contract_receive[key]['mode'] == 'humidity':
            return self.sensor.get_data()[1]
        elif self.contract_receive[key]['mode'] == 'time':
            return time.strftime("%H:%M", time.gmtime())

    #        elif mode == 'manual': return None

    def timer(self):
        if self.contract_receive['illumination']['mode'] == 'manual':
            Gpio.output(self.light_port, self.contract_receive['illumination']['set_light'])
        elif self.contract_receive['illumination']['mode'] == 'time':
            if self.contract_receive['illumination']['off'][11:16] == self.port_handler(
                    'illumination') and self.light_flag:
                Gpio.output(self.light_port, 0)
                self.light_flag = False
            elif self.contract_receive['illumination']['on'][11:16] == self.port_handler(
                    'illumination') and self.light_flag:
                Gpio.output(self.light_port, 1)
                self.light_flag = False
            elif self.port_handler('illumination') not in [self.contract_receive['illumination']['on'][11:16],
                                                           _contract_receive['illumination']['off'][11:16]]:
                self.light_flag = True

    def stop(self):
        self.flag_stop = True
        stop_time = time.time()
        while time.time() - stop_time < 2:
            pass

    def light_report(self):
        if self.light_state != Gpio.input(self.light_port):
            self.light_state = Gpio.input(self.light_port)
            light_contract = {'light_state': self.light_state}
            self.__pipe_parent.send((light_contract, 'sensor_data'))
            with open("./licenses/light.json", 'w') as f:
                f.write(json.dumps(light_contract))
                f.close()

    def write(self):
        with open("./licenses/ports.json", 'w') as f:
            f.write(json.dumps(self.contract_receive))
            f.close()

    def run(self):
        #print('port running')
        while True:
            chan = json.loads(self.__pipe_parent.recv())
            #print(chan)
            if 'state' in chan.keys():
                self.contract_receive = chan['state']
                #print(self.contract_receive)
                self.write()
            self.timer()
            self.light_report()
            if self.flag_stop:
                self.sensor.stop()
                break
