from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import platform
import json
import time
import os
import config
from threading import Thread


class IoT(Thread):
    def __init__(self, client, pipe=None, handler=None):
        self.handler = handler
        self.clientId = client
        self.path = './'
        self.thing_name = self.thing_get()
        self.__pipe_exists = False
        if pipe is not None:
            self.__pipe_exists = True
            self.__pipe_child = pipe
            Thread.__init__(self)
        host = config.HOST
        port = config.PORT
        rootCA_path = self.path+"licenses/root-CA.crt"
        certificate_path = self.path+"licenses/coisa"+self.thing_name+"-certificate.pem.crt"
        private_key_path = self.path+"licenses/coisa"+self.thing_name+"-private.pem.key"

        # Init AWSIoTMQTTShadowClient
        shadow_client = AWSIoTMQTTShadowClient(self.clientId)
        shadow_client.configureEndpoint(host, port)
        shadow_client.configureCredentials(rootCA_path, private_key_path, certificate_path)

        # AWSIoTMQTTShadowClient connection configuration
        shadow_client.configureAutoReconnectBackoffTime(1, 32, 20)
        shadow_client.configureConnectDisconnectTimeout(10)  # 10 sec
        shadow_client.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        shadow_client.connect()

        # Create a device shadow handler, use this to update and delete shadow document
        self.shadow_handler = shadow_client.createShadowHandlerWithName(self.thing_name, True)
        # if callback is not None:
        #    callback_bot = callback(self.shadow_handler)
        #    if handler is not None:
        #        self.shadow_handler.shadowRegisterDeltaCallback(getattr(callback_bot, handler))

            # Listen on deltas
        if handler is not None:
            self.shadow_handler.shadowRegisterDeltaCallback(handler)
        elif self.__pipe_exists:
            self.shadow_handler.shadowRegisterDeltaCallback(self.callback)

    def post(self, message, key):
        if isinstance(message, dict) and isinstance(key, str):
            payload = {'state': {'reported': {key: message}}}
            #print(payload)
            self.shadow_handler.shadowUpdate(json.dumps(payload), self.callback_update, 10)
            return payload
        else: return "The message should be a dict type and the key should be a string type"

    def callback_update(self, payload, response_status, token):
        log = ".\log.txt"
        # Display status and data from update request
        if response_status == "timeout":
            open(log, 'a').write("Update request " + token + " timed out "+self.clientId + " at " +
                                 time.strftime("%H:%M", time.gmtime())+'\n')

        if response_status == "accepted":
            pass
#            payloadDict = json.loads(payload)

        if response_status == "rejected":
            open(log, 'a').write("Update request " + token + " rejected from "+self.clientId + " at " +
                                 time.strftime("%H:%M", time.gmtime())+'\n')

    def thing_get(self):
        if '64' in platform.machine():
            parser = OptionParser(
                version="%prog 1.0",
            )
            options, args = parser.parse_args()
            if len(args) != 1:
                parser.error("Insira o nome da coisa. \n Ex.: python3 {} 1234".format(__file__))
            return str(args[0])

        elif 'arm' in platform.machine():
            return config.THING_NAME

    def callback(self, payload, *_):
        #print(payload)
        self.__pipe_child.send(payload)

    def run(self):
        while True:
            chan = self.__pipe_child.recv()
            if chan:
                msg = chan[0]
                topic = chan[1]
                self.post(msg, topic)
