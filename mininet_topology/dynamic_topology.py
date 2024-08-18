from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import logging


def create_topology(n_switches, n_hosts):
    logging.info(f"Creating topology with {n_switches} switches and {n_hosts} hosts")
    net = Mininet(controller=Controller, link=TCLink, switch=OVSSwitch)

    switches = [net.addSwitch(f"s{i+1}") for i in range(n_switches)]
    hosts = [net.addHost(f"h{i+1}") for i in range(n_hosts)]

    for i, host in enumerate(hosts):
        net.addLink(host, switches[i % n_switches])

    for i in range(n_switches - 1):
        net.addLink(switches[i], switches[i + 1])

    net.start()
    CLI(net)
    net.stop()
