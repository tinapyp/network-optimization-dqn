# Network Optimization with DQN

## Overview

This project implements a network optimization system using Deep Q-Learning (DQN) with Mininet for network simulation and Ryu for network control. The goal is to optimize network routing by training a DQN agent to learn effective routing strategies. The system also includes functionality to visualize and save the best network topology found during training.

## Project Structure

```
network-optimization-dqn/
├── main.py
├── mininet_topology/
│   ├── __init__.py
│   └── dynamic_topology.py
├── requirements.txt
├── ryu_controller/
│   ├── __init__.py
│   ├── dqn_controller.py
│   ├── model/
│   │   ├── model_versioning.py
│   │   └── __init__.py
│   └── network_monitor.py
└── utils/
    └── __init__.py
```

## Setup

### Prerequisites

1. **Docker**: Ensure Docker is installed on your system. You can download Docker from [Docker's official website](https://www.docker.com/products/docker-desktop).

2. **Mininet and Ryu**: This project uses a Docker image that already includes Mininet and Ryu. The base image used is `iwaseyusuke/ryu-mininet`.

### Build the Docker Image

```sh
docker build -t network-optimization-dqn .
```

### Run the Docker Container

```sh
docker run -it network-optimization-dqn
```

### Install Dependencies

Inside the Docker container, dependencies are installed automatically via `requirements.txt`. However, if you need to install them manually, use:

```sh
pip install -r requirements.txt
```

## Usage

1. **Run the Network Simulation**

   Execute the `main.py` script to create and run a network simulation with the specified number of switches and hosts.

   ```sh
   python main.py <number_of_switches> <number_of_hosts>
   ```

   Replace `<number_of_switches>` and `<number_of_hosts>` with the desired values. For example:

   ```sh
   python main.py 3 5
   ```

2. **Visualize and Save Topology**

   After training the model, the system will automatically visualize and save the best network topology. The visualization will be saved as `best_topology.png` in the project directory.

## Components

- **`main.py`**: Initializes the network simulation using Mininet.
- **`mininet_topology/dynamic_topology.py`**: Defines the dynamic network topology using Mininet.
- **`ryu_controller/dqn_controller.py`**: Implements the DQN-based Ryu controller for network optimization.
- **`ryu_controller/model/model_versioning.py`**: Handles saving and loading the best model and topology.
- **`requirements.txt`**: Lists Python package dependencies.

## Visualization

The best network topology is visualized using NetworkX and Matplotlib. The visualization is saved as an image file (`best_topology.png`) and displayed to help analyze the optimal network configuration.