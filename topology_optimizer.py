import random
import networkx as nx
import matplotlib.pyplot as plt
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.link import TCLink
from mininet.clean import cleanup
from mininet.log import setLogLevel
import time
import subprocess


class TopologyOptimizer:
    def __init__(self, min_switches=3, max_switches=10, min_hosts=2, max_hosts=20):
        self.min_switches = min_switches
        self.max_switches = max_switches
        self.min_hosts = min_hosts
        self.max_hosts = max_hosts
        setLogLevel("info")

    def generate_random_topology(self):
        num_switches = random.randint(self.min_switches, self.max_switches)
        num_hosts = random.randint(self.min_hosts, self.max_hosts)

        switches = [f"s{i+1}" for i in range(num_switches)]
        hosts = [f"h{i+1}" for i in range(num_hosts)]

        # Create a random topology for switches
        G = nx.connected_watts_strogatz_graph(num_switches, 3, 0.5)
        links = list(G.edges())

        # Convert node numbers to switch names
        links = [(f"s{a+1}", f"s{b+1}") for a, b in links]

        # Connect hosts to random switches
        for host in hosts:
            switch = random.choice(switches)
            links.append((host, switch))

        return switches, hosts, links

    def simulate_topology(self, switches, hosts, links):
        net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink)

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
        net.addController("c0")

        # Start the network
        net.start()

        # Wait for the network to stabilize
        time.sleep(5)

        # Measure performance metrics
        avg_latency = self.measure_latency(net, hosts)
        avg_bandwidth = self.measure_bandwidth(net, hosts)
        packet_loss = self.measure_packet_loss(net, hosts)

        # Stop the network
        net.stop()
        cleanup()

        # Calculate a performance score (lower is better)
        performance_score = avg_latency + (1 / avg_bandwidth) + (100 * packet_loss)
        return performance_score

    def measure_latency(self, net, hosts):
        total_latency = 0
        num_pairs = min(
            10, len(hosts) * (len(hosts) - 1) // 2
        )  # Limit to 10 pairs for efficiency
        pairs = random.sample(
            [(h1, h2) for i, h1 in enumerate(hosts) for h2 in hosts[i + 1 :]], num_pairs
        )

        for h1, h2 in pairs:
            latency = net.ping([net.get(h1), net.get(h2)], timeout=1)
            if latency:
                total_latency += latency

        return total_latency / num_pairs if num_pairs > 0 else float("inf")

    def measure_bandwidth(self, net, hosts):
        total_bandwidth = 0
        num_pairs = min(5, len(hosts) // 2)  # Limit to 5 pairs for efficiency
        pairs = random.sample(
            list(zip(hosts[:num_pairs], hosts[num_pairs : 2 * num_pairs])), num_pairs
        )

        for h1, h2 in pairs:
            h1_obj, h2_obj = net.get(h1), net.get(h2)
            server = h1_obj.popen(f"iperf -s -p 5001")
            time.sleep(1)  # Wait for the server to start
            client_output = h2_obj.cmd(f"iperf -c {h1_obj.IP()} -p 5001 -t 5")
            server.terminate()

            bandwidth = float(client_output.split("Mbits/sec")[0].split()[-1])
            total_bandwidth += bandwidth

        return total_bandwidth / num_pairs if num_pairs > 0 else 0

    def measure_packet_loss(self, net, hosts):
        total_packet_loss = 0
        num_pairs = min(
            10, len(hosts) * (len(hosts) - 1) // 2
        )  # Limit to 10 pairs for efficiency
        pairs = random.sample(
            [(h1, h2) for i, h1 in enumerate(hosts) for h2 in hosts[i + 1 :]], num_pairs
        )

        for h1, h2 in pairs:
            h1_obj, h2_obj = net.get(h1), net.get(h2)
            ping_output = h1_obj.cmd(f"ping -c 10 -q {h2_obj.IP()}")
            packet_loss = float(ping_output.split("%")[0].split()[-1]) / 100
            total_packet_loss += packet_loss

        return total_packet_loss / num_pairs if num_pairs > 0 else 1

    def optimize_topology(self, num_iterations=10):
        best_topology = None
        best_performance = float("inf")

        for _ in range(num_iterations):
            switches, hosts, links = self.generate_random_topology()
            performance = self.simulate_topology(switches, hosts, links)

            if performance < best_performance:
                best_performance = performance
                best_topology = (switches, hosts, links)

            print(f"Iteration {_+1}/{num_iterations}: Performance = {performance}")

        self.visualize_topology(*best_topology)
        return best_topology

    def visualize_topology(self, switches, hosts, links):
        G = nx.Graph()
        G.add_edges_from(links)

        pos = nx.spring_layout(G)
        plt.figure(figsize=(12, 8))
        nx.draw_networkx_nodes(
            G, pos, nodelist=switches, node_color="lightblue", node_size=500
        )
        nx.draw_networkx_nodes(
            G, pos, nodelist=hosts, node_color="lightgreen", node_size=300
        )
        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_labels(G, pos)

        plt.title("Optimized Network Topology")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig("optimized_topology.png")
        plt.close()


if __name__ == "__main__":
    optimizer = TopologyOptimizer()
    best_topology = optimizer.optimize_topology()
    print("Best topology:", best_topology)
