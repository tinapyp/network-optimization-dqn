from mininet_topology.dynamic_topology import create_topology
import sys


def run_network_experiment(n_switches, n_hosts):
    create_topology(n_switches, n_hosts)


if __name__ == "__main__":
    n_switches = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    n_hosts = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    run_network_experiment(n_switches, n_hosts)
