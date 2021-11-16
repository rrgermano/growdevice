from ports import Ports
from ssh import SSH
from wps import WPS

'''processes = [Ports, SSH, WPS]
construct_processes = []
for process in processes:
    pipe1 = Pipe()
    pipe2 = Pipe()
    p = process(pipe1, pipe2)
    construct_processes.append(p)

wps = WPS()
construct_processes.append(wps)'''

wps = WPS()
ports = Ports()
ssh = SSH()

construct_processes = [wps, ports, ssh]

try:
    for process in construct_processes:
        process.start()
except KeyboardInterrupt:
    for process in construct_processes:
        process.stop()
    exit(0)
