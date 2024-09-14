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
sudo apt-get install openvswitch-switch
sudo apt-get install mininet
```

2. Install Python from https://repo.anaconda.com/miniconda/

```Bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-py310_24.5.0-0-Linux-aarch64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```

3. Then install Depedencies

```bash
pip install setuptools==57.5.0
pip install h5py==3.6.0
pip install -r requirements.txt
```

## Usage

1. Run the topology optimizer to find the best network topology:

```bash
sudo /home/user/miniconda3/bin/python topology_optimizer.py
```

\*Note change `user` with you user

This will generate an optimized topology and save it as "optimized_topology.png".

2. Start the Ryu controller in a separate terminal:

```bash
ryu-manager ryu_controller.py
```

3. Run the main script to create the Mininet network and start the simulation:

```bash
sudo /home/user/miniconda3/bin/python main.py
```

\*Note change `user` with you user

## Project Structure

- `main.py`: The entry point of the application. It creates the Mininet network and starts the simulation.
- `ryu_controller.py`: Implements the Ryu controller with DQN-based optimization.
- `topology_optimizer.py`: Generates and optimizes network topologies based on performance metrics.

## Customization

You can customize the project by modifying the following parameters:

- In `topology_optimizer.py`: Adjust `min_switches`, `max_switches`, `min_hosts`, and `max_hosts` in the `TopologyOptimizer` class to control the range of network sizes.
- In `ryu_controller.py`: Modify the `DQNAgent` class parameters to fine-tune the DQN algorithm.
- In `main.py`: Add functions to dynamically modify the network structure during runtime.

## Extra

If get eror folder exist run this code below

```bash
sudo mn -c
```
