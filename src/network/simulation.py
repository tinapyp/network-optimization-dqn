from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel
import matplotlib.pyplot as plt
import networkx as nx
import time
import numpy as np


class NetworkSimulation:
    def __init__(self):
        self.net = None
        self.best_topology = None
        self.best_performance = float("-inf")
        self.switches = []
        self.hosts = []

    def create_network(self):
        self.net = Mininet(
            controller=RemoteController, switch=OVSKernelSwitch, link=TCLink
        )

        # Add switches
        for i in range(4):
            switch = self.net.addSwitch(f"s{i+1}")
            self.switches.append(switch)

        # Add hosts
        for i in range(4):
            host = self.net.addHost(f"h{i+1}")
            self.hosts.append(host)

        # Add links
        self.net.addLink(self.hosts[0], self.switches[0])
        self.net.addLink(self.hosts[1], self.switches[1])
        self.net.addLink(self.hosts[2], self.switches[2])
        self.net.addLink(self.hosts[3], self.switches[3])
        self.net.addLink(self.switches[0], self.switches[1])
        self.net.addLink(self.switches[1], self.switches[2])
        self.net.addLink(self.switches[2], self.switches[3])
        self.net.addLink(self.switches[3], self.switches[0])

        # Add controller
        self.net.addController(
            "c0", controller=RemoteController, ip="127.0.0.1", port=6633
        )

        # Start network
        self.net.start()

    def get_state(self):
        stats = []
        for switch in self.switches:
            for intf in switch.intfList():
                if intf.link:
                    stats.extend([intf.stats()["rxbytes"], intf.stats()["txbytes"]])
        return np.array(stats).reshape(1, -1)

    def take_action(self, action):
        actions = [
            (self.switches[0], self.switches[1], 1),
            (self.switches[1], self.switches[2], 1),
            (self.switches[2], self.switches[3], 1),
            (self.switches[3], self.switches[0], 1),
            (self.switches[0], self.switches[1], 2),
            (self.switches[1], self.switches[2], 2),
            (self.switches[2], self.switches[3], 2),
            (self.switches[3], self.switches[0], 2),
        ]

        if action < len(actions):
            s1, s2, weight = actions[action]
            self.net.configLinkStatus(s1.name, s2.name, "down")
            self.net.configLinkStatus(s1.name, s2.name, "up")
            link = self.net.linksBetween(s1, s2)[0]
            link.intf1.config(bw=weight)
            link.intf2.config(bw=weight)

    def get_reward(self):
        h1, h4 = self.hosts[0], self.hosts[3]
        h1.cmd(f"iperf -c {h4.IP()} -t 5 -i 1 > iperf_result &")
        time.sleep(6)
        result = h1.cmd("cat iperf_result")
        lines = result.split("\n")
        if len(lines) > 1:
            last_line = lines[-2]
            throughput = float(last_line.split()[-2])
            return throughput
        return 0

    def update_best_topology(self, performance):
        if performance > self.best_performance:
            self.best_performance = performance
            self.best_topology = self.get_current_topology()

    def get_current_topology(self):
        topology = {}
        for switch in self.switches:
            topology[switch.name] = []
            for intf in switch.intfList():
                if intf.link:
                    connected_node = (
                        intf.link.intf1.node
                        if intf.link.intf1.node != switch
                        else intf.link.intf2.node
                    )
                    topology[switch.name].append(
                        (
                            connected_node.name,
                            intf.stats()["rxbytes"],
                            intf.stats()["txbytes"],
                        )
                    )
        return topology

    def visualize_best_topology(self):
        if self.best_topology:
            G = nx.Graph()
            for switch, connections in self.best_topology.items():
                G.add_node(switch)
                for connected_node, rxbytes, txbytes in connections:
                    G.add_edge(switch, connected_node, weight=(rxbytes + txbytes) / 2)

            pos = nx.spring_layout(G)
            nx.draw(
                G,
                pos,
                with_labels=True,
                node_color="lightblue",
                node_size=500,
                font_size=10,
                font_weight="bold",
            )
            edge_labels = nx.get_edge_attributes(G, "weight")
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

            plt.title("Best Network Topology")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig("/app/best_topology.png")
            plt.close()
