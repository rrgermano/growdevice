import socket
import select
import sys
from multiprocessing import Process, Pipe
from threading import Thread
import paramiko
import json
import subprocess
import time

import AWSIoT
import config


class SSH(Process):


    def __init__(self, client_id="SSH"):
        self.client_id = client_id
        self.export_ip = False
        self.flag_stop = False
        self.__pipe_parent, self.__pipe_child = Pipe()
        self.iot = AWSIoT.IoT(self.client_id, pipe=self.__pipe_child).start()
        Process.__init__(self)

    def handler(self, chan, host, port, transport):
        sock = socket.socket()
        try:
            sock.connect((host, port))
        except Exception as e:
#            verbose("Forwarding request to %s:%d failed: %r" % (host, port, e))
            return

#        verbose("Connected!  Tunnel open %r -> %r -> %r" % (chan.origin_addr, chan.getpeername(), (host, port)))
        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)

#        verbose("Tunnel closed from %r" % (chan.origin_addr,))
        chan.close()
        sock.close()
        transport.close()
        contract_send = {"opened": False}
        self.export_ip = False
        self.__pipe_parent.send((contract_send, "SSH"))
        #self.iot.post_()
        return

    def reverse_forward_tunnel(self, server_port, remote_host, remote_port, transport):
        while True:
            try:
                transport.request_port_forward("", server_port)
#                verbose("Now forwarding remote port %d"% (server_port))
                contract_send = {"Port": server_port, "opened": True, "public_ip": ""}
                self.__pipe_parent.send((contract_send, "SSH"))
                #self.iot.post_()
                transport.set_keepalive(50)
                break
            except Exception:
                server_port +=1
                pass

        while True:
            chan = transport.accept(120)
            if chan is None:
                continue
            thr = Thread(target=self.handler, args=(chan, remote_host, remote_port, transport))
            thr.setDaemon(True)
            thr.start()
            break
        return

    def stop(self):
        self.flag_stop = True

    def run(self):
        user = config.EC2_USER
        key = config.EC2_KEY
        server = (config.EC2_SERVER, config.LOCAL_PORT)
        remote = ('localhost', config.LOCAL_PORT)
        remote_port = config.REMOTE_PORT
        public_ip = str(subprocess.run(['curl', 'ifconfig.me'], capture_output=True).stdout).split("'")[1]
        while True:
            chan = json.loads(self.__pipe_parent.recv())
            # print(chan)
            if 'state' in chan.keys():
                contract_receive = chan['state']['SSH']
            if contract_receive['open_request'] and not self.export_ip:
                contract_send = {"public_ip": public_ip}
                self.__pipe_parent.send((contract_send, "SSH"))
                #self.iot.post_()
                self.export_ip = True
                time.sleep(2)
            if contract_receive['open']:
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())

                try:
                    client.connect(
                        server[0],
                        server[1],
                        username=user,
                        key_filename=key,
                    )
                except Exception as e:
#                    print("*** Failed to connect to %s:%d: %r" % (server[0], server[1], e))
                    sys.exit(1)
                try:
                    self.reverse_forward_tunnel(
                        remote_port, remote[0], remote[1], client.get_transport()
                    )

                except (KeyboardInterrupt):
#                    print("C: Port forwarding stopped.")
                    sys.exit(0)

            if self.flag_stop:
                break




if __name__ == '__main__':
    ssh = SSH()
    ssh.start()