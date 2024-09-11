#!/usr/bin/env python3
import os
import sys
import time
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from topology_optimizer import TopologyOptimizer
from mininet.link import TCLink


def create_network(switches, hosts, links):
    net = Mininet(controller=RemoteController, switch=OVSSwitch, link=TCLink)

    # Add switches
    switch_objects = {}
    for s in switches:
        switch_objects[s] = net.addSwitch(s)

    # Add hosts
    host_objects = {}
    for h in hosts:
        host_objects[h] = net.addHost(h)

    # Add links
    for src, dst in links:
        src_obj = switch_objects.get(src) or host_objects.get(src)
        dst_obj = switch_objects.get(dst) or host_objects.get(dst)
        net.addLink(src_obj, dst_obj)

    # Add controller
    net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6633)

    return net


def run_simulation(net, duration=60):
    net.start()
    print("Running simulation for", duration, "seconds...")
    time.sleep(duration)
    net.stop()


def main():
    setLogLevel("info")

    optimizer = TopologyOptimizer()
    best_topology = optimizer.optimize_topology()

    if best_topology:
        switches, hosts, links = best_topology
        print(f"Best topology found: {len(switches)} switches, {len(hosts)} hosts")

        net = create_network(switches, hosts, links)
        run_simulation(net)
    else:
        print("Failed to find an optimal topology")


if __name__ == "__main__":
    main()
