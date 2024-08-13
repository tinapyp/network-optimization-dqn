import logging
from ryu_controller.dqn_controller import DQNController
from mininet_topology.dynamic_topology import create_topology
from ryu.cmd import manager

logging.basicConfig(filename='logs/network_optimization.log', level=logging.INFO)

def start_ryu_controller():
    app_manager = manager.main(['ryu.cmd.manager', 'ryu_controller.dqn_controller'])

def main(n_switches, n_hosts):
    try:
        create_topology(n_switches, n_hosts)
        start_ryu_controller()
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    import sys
    n_switches = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    n_hosts = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    main(n_switches, n_hosts)
