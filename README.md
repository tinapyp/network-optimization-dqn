# SDN Network Optimization Project

This project implements an SDN (Software-Defined Networking) network optimization system using Deep Q-Learning (DQN) with Mininet for network simulation and Ryu for network control. The system dynamically optimizes network topology and routing based on real-time performance metrics.

## Features

- Automatic topology optimization using performance metrics
- Dynamic addition and removal of switches and hosts
- DQN-based network optimization for improved performance
- Real-time network state monitoring and visualization

## Prerequisites

- Ubuntu 20.04 or later
- Python 3.8 or later
- Mininet
- Ryu SDN Framework
- TensorFlow
- NetworkX
- Matplotlib

## Installation

1. Update your system and install required packages:

```bash
sudo apt-get update
sudo apt-get install -y mininet python3-ryu python3-networkx python3-matplotlib python3-tensorflow
pip3 install mininet
```

2. Clone this repository:

```bash
git clone https://github.com/yourusername/sdn_optimization_project.git
cd sdn_optimization_project
```

## Usage

1. Run the topology optimizer to find the best network topology:

```bash
sudo python3 topology_optimizer.py
```

This will generate an optimized topology and save it as "optimized_topology.png".

2. Start the Ryu controller in a separate terminal:

```bash
ryu-manager ryu_controller.py
```

3. Run the main script to create the Mininet network and start the simulation:

```bash
sudo python3 main.py
```

## Project Structure

- `main.py`: The entry point of the application. It creates the Mininet network and starts the simulation.
- `ryu_controller.py`: Implements the Ryu controller with DQN-based optimization.
- `topology_optimizer.py`: Generates and optimizes network topologies based on performance metrics.

## Customization

You can customize the project by modifying the following parameters:

- In `topology_optimizer.py`: Adjust `min_switches`, `max_switches`, `min_hosts`, and `max_hosts` in the `TopologyOptimizer` class to control the range of network sizes.
- In `ryu_controller.py`: Modify the `DQNAgent` class parameters to fine-tune the DQN algorithm.
- In `main.py`: Add functions to dynamically modify the network structure during runtime.
