from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import logging

def create_topology(n_switches, n_hosts):
    logging.info(f"Creating topology with {n_switches} switches and {n_hosts} hosts")
    net = Mininet(controller=Controller, link=TCLink, switch=OVSSwitch)

    switches = []
    for i in range(n_switches):
        switch = net.addSwitch(f's{i+1}')
        switches.append(switch)

    hosts = []
    for i in range(n_hosts):
        host = net.addHost(f'h{i+1}')
        hosts.append(host)
    
    for i, host in enumerate(hosts):
        net.addLink(host, switches[i % n_switches])

    for i in range(n_switches - 1):
        net.addLink(switches[i], switches[i + 1])

    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    import sys
    n_switches = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    n_hosts = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    create_topology(n_switches, n_hosts)
