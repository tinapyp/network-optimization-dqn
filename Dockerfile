# Use an official Python image as the base
FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    mininet \
    gcc \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    pkg-config \
    libhdf5-dev \
    iputils-ping \
    iproute2 \
    net-tools \
    sudo \
    openvswitch-switch \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the project files to the working directory
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the OpenFlow port used by Ryu (6633)
EXPOSE 6633

# Start Open vSwitch service and run the Ryu controller along with the simulation script
CMD ["bash", "-c", "service openvswitch-switch start && ryu-manager src/controller/ryu_controller.py & python src/main.py"]
