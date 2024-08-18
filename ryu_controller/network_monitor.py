import logging
import time


class NetworkMonitor:
    def __init__(self, dqn_controller):
        self.dqn_controller = dqn_controller

    def start_monitoring(self):
        logging.info("Starting network monitoring...")
        while True:
            self.log_network_metrics()
            time.sleep(60)  # Log metrics every 60 seconds

    def log_network_metrics(self):
        latency = self.dqn_controller.network_latency
        throughput = self.dqn_controller.network_throughput
        logging.info(f"Network Latency: {latency}")
        logging.info(f"Network Throughput: {throughput}")
